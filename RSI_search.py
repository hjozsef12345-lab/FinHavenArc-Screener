import json
import os
import sys
import threading
import time
import traceback
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests
import yfinance as yf

import watchlists   # the *_watchlist_by_suffix dictionaries (copied here unchanged)
from markets import BASE_DIR, LOG_DIR, NY_TZ, RUNS, exchange_of, write_log_line

# ==================================================================================
# TELEGRAM
# ==================================================================================
def _load_secret(name):
    value = os.environ.get(name)          # the environment variable takes priority
    if value:
        return value
    path = os.path.join(BASE_DIR, "secrets.env")
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                key, _, val = line.strip().partition("=")
                if key == name:
                    return val.strip()
    except OSError:
        pass
    raise RuntimeError(f"Missing secret: {name}")

TELEGRAM_TOKEN = _load_secret("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = ("8612990644")     # your personal chat ID
# Optional ADMIN notification (only for you): crash / download error. None = disabled.
# The same error sends a message at most once every 30 minutes.
TELEGRAM_ADMIN_CHAT_ID = None

TELEGRAM_BATCH_INTERVAL_SEC = 5
TELEGRAM_MAX_LEN = 3900                     # the hard limit is 4096
TELEGRAM_SEPARATOR = "\n\n──────────\n\n"

# ==================================================================================
# SETTINGS
# ==================================================================================
# period = amount downloaded on a COLD START; max_age = a cache older than this many minutes gets refreshed;
# trim = cache size (number of candles)
TF_5M  = {"interval": "5m",  "period": "5d",  "minutes": 5,  "max_age": 4,  "trim": 200}
TF_15M = {"interval": "15m", "period": "5d",  "minutes": 15, "max_age": 14, "trim": 200}
TF_1H  = {"interval": "60m", "period": "2mo", "minutes": 60, "max_age": 59, "trim": 400}   # the 4H is built from this
# China: the trading day is 4 hours, so 1 "4H" candle = 1 day; the 60-candle warm-up needs 60 days.
COLD_PERIOD_1H_OVERRIDE = {"china": "6mo"}
REFRESH_PERIOD = "1d"            # on a normal refresh we re-request this much

RSI_PERIOD = ATR_PERIOD = BB_PERIOD = ADX_PERIOD = 14
BB_PERIOD = 20
BB_STD = 2
WARMUP_BARS = 60                 # the longest period (20) x 3

# 4H trend filter
ADX_4H_MIN = 20
RSI_4H_LONG_MIN = 50
RSI_4H_SHORT_MAX = 50

# Fresh-candle protection: if the last closed 5M candle is older than this (minutes), the stock is skipped
# (exchange closed / holiday / no fresh Yahoo data).
MAX_SIGNAL_BAR_AGE_MIN = 60

# Exit (SL/TP) based on the 15M ATR
SL_ATR_MULT = 4.0
TP_ATR_MULT = 8.0

# Reversal engine
REVERSAL_RVOL_PERIOD = 20
REVERSAL_RVOL_MIN = 1.30
REVERSAL_RVOL_STRONG = 1.70
REVERSAL_SCORE_MIN = 6
REVERSAL_SCORE_STRONG_AGAINST_TREND = 8   # for a signal against a strong 4H trend
REVERSAL_SWING_LOOKBACK = 5
REVERSAL_MIN_BODY_RATIO = 0.25
ALERT_COOLDOWN_MIN = 60                   # between alerts in the same direction (a change of direction passes through)

# Download batching (Yahoo rate-limit protection)
BATCH_SIZE = 250
BATCH_PAUSE_SEC = 5

# Catching up on missed candles based on the age of the cache's last candle:
#   <= 6 hours      : normal refresh (REFRESH_PERIOD)
#   <= 6 days       : CATCHUP_PERIOD (after a weekend / holiday / outage, overwrites partial candles)
#   longer          : full cold start
CATCHUP_AFTER_HOURS = 6
CATCHUP_PERIOD = "5d"
CATCHUP_MAX_DAYS = 6

STATE_DIR = os.path.join(BASE_DIR, "state")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
LOCK_DIR = os.path.join(BASE_DIR, "lock")
OUTBOX_PATH = os.path.join(STATE_DIR, "telegram_outbox.json")


# ==================================================================================
# SESSION HELPERS (in one place: filtering, VWAP, 4H and the gap check all use these)
# ==================================================================================
def session_ids(index, ex):
    """Per-candle session number (0, 1, ...), -1 outside a session. Plus the local-time index."""
    local = index.tz_convert(ex["tz"])
    mins = np.asarray(local.hour * 60 + local.minute)
    ids = np.full(len(index), -1)
    for n, (start, end) in enumerate(ex["sessions"]):
        ids[(mins >= start) & (mins < end)] = n
    return ids, local


def filter_to_market_sessions(df, ex):
    """Only candles within the official sessions (drops Yahoo's out-of-session data)."""
    if df.empty:
        return df
    ids, _ = session_ids(df.index, ex)
    return df[ids >= 0]


def drop_unclosed_candle(df, interval_minutes):
    """Drops the last candle if it has not closed yet."""
    if df.empty:
        return df
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index, utc=True, errors="coerce")
        df = df[~df.index.isna()]
        if df.empty:
            return df
    tz = df.index.tz
    now = pd.Timestamp.now(tz=tz) if tz is not None else pd.Timestamp.now()
    if df.index[-1] + pd.Timedelta(minutes=interval_minutes) > now:
        return df.iloc[:-1]
    return df


def warn_on_unexpected_gap(df, interval_minutes, symbol, ex):
    """A real data gap: a missing timestamp on the same day, within the same session.
    Must be called on the raw Yahoo data, BEFORE dropna (a NaN row + zero volume = no trade, not an error)."""
    if len(df) < 2:
        return
    ids, local = session_ids(df.index, ex)
    dates = np.asarray(local.date)
    gaps = np.diff(df.index.values).astype("timedelta64[s]").astype(int) / 60.0
    bad = (
        (gaps > interval_minutes * 1.5)
        & (ids[1:] == ids[:-1]) & (ids[1:] >= 0)
        & (dates[1:] == dates[:-1])
    )
    if bad.any():
        pos = np.flatnonzero(bad)
        print(f"WARNING: {symbol} {interval_minutes}M: {len(pos)} DATA GAP(S) "
              f"(first: {local[pos[0]]} -> {local[pos[0] + 1]}, {gaps[pos[0]]:.0f} min)")


def compute_session_vwap(df, ex):
    """Session VWAP: restarts daily (the exchange's local day), continues after the break between sessions,
    NaN outside a session."""
    ids, local = session_ids(df.index, ex)
    inside = ids >= 0
    vol = df["Volume"].fillna(0).where(inside, 0.0)
    typical = (df["High"] + df["Low"] + df["Close"]) / 3.0
    pv = (typical * vol).where(inside, 0.0)
    day = pd.Series(local.date, index=df.index)
    cum_vol = vol.groupby(day).cumsum()
    vwap = pv.groupby(day).cumsum() / cum_vol.where(cum_vol > 0)
    return vwap.where(inside)


def resample_to_4h(df_1h, ex):
    """4H candles from the hourly ones (Yahoo does not provide 4H). The blocks are formed by trading minutes
    counted from the open (the lunch break does not count); the last unclosed block is dropped."""
    if df_1h.empty:
        return df_1h
    local = df_1h.index.tz_convert(ex["tz"])
    mins = np.asarray(local.hour * 60 + local.minute)
    elapsed = np.full(len(mins), -1)
    offset = 0
    for start, end in ex["sessions"]:
        inside = (mins >= start) & (mins < end)
        elapsed[inside] = offset + (mins[inside] - start)
        offset += end - start
    total_minutes = offset

    keep = elapsed >= 0
    if not keep.any():
        return df_1h.iloc[0:0]
    d = df_1h[keep]
    el = elapsed[keep]
    d = d.assign(_t=d.index, _day=np.asarray(local.date)[keep], _block=el // 240)
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum", "_t": "first"}
    out = d.groupby(["_day", "_block"]).agg(agg)
    out.index = pd.DatetimeIndex(out.pop("_t"))

    # the last block is closed if the last hourly candle reaches the end of the block (or the end of the session)
    block_end = min((int(el[-1] // 240) + 1) * 240, total_minutes)
    if int(el[-1]) + 60 < block_end:
        out = out.iloc[:-1]
    return out


# ==================================================================================
# INDICATORS
# ==================================================================================
def _true_range(high, low, close):
    prev = close.shift(1)
    return pd.concat([high - low, (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)


def _wilder(series, period):
    return series.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def compute_rsi(close, period=14):
    delta = close.diff()
    avg_gain = _wilder(delta.clip(lower=0), period)
    avg_loss = _wilder(-delta.clip(upper=0), period)
    return 100 - (100 / (1 + avg_gain / avg_loss))


def compute_atr(high, low, close, period=14):
    return _wilder(_true_range(high, low, close), period)


def compute_bollinger_width(close, period=20, num_std=2.0):
    """Relative band width (%), a measure of volatility."""
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    return (2 * num_std * std) / sma * 100


def compute_adx(high, low, close, period=14):
    """ADX, +DI, -DI (Wilder smoothing)."""
    up, down = high.diff(), -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    atr = compute_atr(high, low, close, period)
    plus_di = 100 * _wilder(plus_dm, period) / atr
    minus_di = 100 * _wilder(minus_dm, period) / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return _wilder(dx, period), plus_di, minus_di


def compute_relative_volume(volume, period=20):
    """Recent RVOL: the current 5M volume / the MEDIAN volume of the previous 'period' candles.
    (Not a time-of-day RVOL; the median is less distorted by an occasional outlier candle.)"""
    volume = pd.to_numeric(volume, errors="coerce")
    baseline = volume.shift(1).rolling(period, min_periods=max(5, period // 2)).median()
    return (volume / baseline.replace(0, np.nan)).astype(float)


# ==================================================================================
# EARLY REVERSAL ENGINE (5M price action + volume + RVOL + VWAP + RSI)
# ==================================================================================
def compute_features(df, rvol_series, rsi_series):
    """Features of the last 5M candle. LONG and SHORT are mirror images of the same logic, so we
    return them with identical keys per direction:
        trap        : failed breakdown (LONG) / failed breakout (SHORT)
        structure   : higher low / lower high
        rejection   : bullish / bearish rejection (long wick)
        strength    : strong close at the appropriate end of the candle
        vol_pressure: volume expansion on a candle closing in the direction
        rsi_turn    : the RSI is turning (versus 1 and 3 candles earlier)
    """
    empty_side = dict(trap=False, structure=False, rejection=False,
                      strength=False, vol_pressure=False, rsi_turn=False)
    if len(df) < 8:
        return {"rvol": float("nan"), "vol_exp": False,
                "LONG": dict(empty_side), "SHORT": dict(empty_side)}

    last = df.iloc[-1]
    o, h, l, c = (float(last[k]) for k in ("Open", "High", "Low", "Close"))
    rng = h - l
    body = abs(c - o)
    upper_wick = max(h - max(o, c), 0.0)
    lower_wick = max(min(o, c) - l, 0.0)
    has_range = rng > 0
    close_pos = (c - l) / rng if has_range else None       # 0 = near the low, 1 = near the high
    body_ratio = body / rng if has_range else None

    window = df.iloc[-(REVERSAL_SWING_LOOKBACK + 1):-1]
    local_low, local_high = float(window["Low"].min()), float(window["High"].max())

    lows = df["Low"].iloc[-5:-1]
    highs = df["High"].iloc[-5:-1]
    mid = len(lows) // 2

    volume = df["Volume"].astype(float)
    vol_exp = float(volume.iloc[-1]) > float(volume.iloc[-2]) * 1.20
    prev_close = float(df["Close"].iloc[-2])

    rvol_value = rvol_series.iloc[-1]
    rsi_1 = float(rsi_series.iloc[-1] - rsi_series.iloc[-2])
    rsi_3 = float(rsi_series.iloc[-1] - rsi_series.iloc[-4])
    body_ok = has_range and body_ratio >= REVERSAL_MIN_BODY_RATIO

    long_side = dict(
        trap=l < local_low and c > local_low,
        structure=float(lows.iloc[mid:].min()) > float(lows.iloc[:mid].min()),
        rejection=has_range and c > o and lower_wick > body * 0.8 and close_pos >= 0.60,
        strength=body_ok and c > o and close_pos >= 0.70,
        vol_pressure=vol_exp and c > prev_close,
        rsi_turn=rsi_1 > 0 and rsi_3 > 0,
    )
    short_side = dict(
        trap=h > local_high and c < local_high,
        structure=float(highs.iloc[mid:].max()) < float(highs.iloc[:mid].max()),
        rejection=has_range and c < o and upper_wick > body * 0.8 and close_pos <= 0.40,
        strength=body_ok and c < o and close_pos <= 0.30,
        vol_pressure=vol_exp and c < prev_close,
        rsi_turn=rsi_1 < 0 and rsi_3 < 0,
    )
    return {
        "rvol": float(rvol_value) if pd.notna(rvol_value) else float("nan"),
        "vol_exp": vol_exp,
        "LONG": long_side,
        "SHORT": short_side,
    }


def is_valid_reversal_setup(direction, feat):
    """The score alone is not enough: it requires RVOL, a real price action event AND directional confirmation."""
    rvol = feat["rvol"]
    if pd.isna(rvol) or rvol < REVERSAL_RVOL_MIN:
        return False
    f = feat[direction]
    price_action = f["trap"] or f["structure"] or f["rejection"]
    confirmation = f["strength"] or f["vol_pressure"] or f["rsi_turn"]
    return bool(price_action and confirmation)


def calculate_reversal_score(direction, feat, price, vwap, trend_context):
    f = feat[direction]
    rvol = feat["rvol"]
    long = direction == "LONG"

    score = 2 * f["trap"] + 2 * f["structure"]
    score += f["rejection"] + f["strength"] + f["vol_pressure"] + feat["vol_exp"] + f["rsi_turn"]

    if not pd.isna(rvol):
        score += rvol >= REVERSAL_RVOL_MIN
        score += rvol >= REVERSAL_RVOL_STRONG

    if not pd.isna(vwap):
        if long:
            score += 2 * (price >= vwap)                         # VWAP reclaim
            score += vwap * 0.997 < price < vwap                 # near VWAP
        else:
            score += 2 * (price <= vwap)                         # VWAP rejection
            score += vwap < price < vwap * 1.003                 # near VWAP

    score += trend_context == ("BULLISH" if long else "BEARISH")
    return int(score)


# ==================================================================================
# CACHE
# ==================================================================================
def cache_file_path(market_arg, label):
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{market_arg}_{label}.pkl")


def to_utc_index(df):
    """The index is uniformly UTC, timezone-aware (otherwise "Cannot join tz-naive with tz-aware")."""
    if df is None or df.empty:
        return df
    idx = df.index
    if not isinstance(idx, pd.DatetimeIndex):
        df = df.set_axis(pd.to_datetime(idx, utc=True, errors="coerce"), axis=0)
        return df[~df.index.isna()]
    if idx.tz is None:
        return df.set_axis(idx.tz_localize("UTC"), axis=0)
    if str(idx.tz) != "UTC":
        return df.set_axis(idx.tz_convert("UTC"), axis=0)
    return df


def load_cache(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return to_utc_index(pd.read_pickle(path))
    except Exception:
        return pd.DataFrame()


def save_cache(path, df):
    tmp = f"{path}.tmp"
    try:
        df.to_pickle(tmp)
        os.replace(tmp, path)      # atomic replace
    except Exception as e:
        print(f"WARNING: failed to save the cache ({path}): {e}")


def is_valid_1h_cache(df, min_rows=100):
    """Whether the 1H structure is safe: no NaN/duplicate timestamps, no fractional minutes
    (candles starting at :30 are fine)."""
    if df is None or df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return False
    idx = df.index
    return bool(len(df) >= min_rows and not idx.hasnans and idx.is_unique
                and (idx == idx.floor("min")).all())


def merge_and_dedupe(cache_df, fresh_df):
    """Merge by timestamp AND ticker: fresh data overwrites old, but whatever is missing from the fresh
    download (failed batch, NaN) does NOT delete the value in the cache."""
    if cache_df.empty:
        return to_utc_index(fresh_df)
    fresh = to_utc_index(fresh_df)
    old = to_utc_index(cache_df)
    fresh = fresh[~fresh.index.duplicated(keep="last")]
    old = old[~old.index.duplicated(keep="last")]
    return fresh.combine_first(old).sort_index()


def pick_refresh_period(cache_age, cold_period):
    if cache_age <= pd.Timedelta(hours=CATCHUP_AFTER_HOURS):
        return REFRESH_PERIOD
    if cache_age <= pd.Timedelta(days=CATCHUP_MAX_DAYS):
        return CATCHUP_PERIOD
    return cold_period


def download_in_batches(symbols, period, interval):
    if not symbols:
        return pd.DataFrame()
    frames = []
    for i in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[i:i + BATCH_SIZE]
        try:
            data = yf.download(batch, period=period, interval=interval,
                               group_by="ticker", progress=False, prepost=False)
            # An empty batch must NOT get into the concatenation (tz-naive index -> crash).
            if data is not None and not data.empty:
                frames.append(to_utc_index(data))
            else:
                print(f"⚠️ Empty batch ({i}-{i + len(batch)}), skipped.")
        except Exception as e:
            print(f"Error downloading batch ({i}-{i + len(batch)}): {e}")
        if i + BATCH_SIZE < len(symbols):
            print(f"⏳ {i + len(batch)} stocks downloaded. Pausing {BATCH_PAUSE_SEC} s to protect against Yahoo rate limits...")
            time.sleep(BATCH_PAUSE_SEC)
    if not frames:
        return pd.DataFrame()
    return frames[0] if len(frames) == 1 else pd.concat(frames, axis=1)


def get_or_refresh_cache(market_arg, label, symbols, tf, cold_period=None):
    """Staleness-based refresh: fresh cache -> no download; otherwise an amount that depends on the cache's age.
    Returns: (data, whether it was refreshed)."""
    cold_period = cold_period or tf["period"]
    path = cache_file_path(market_arg, label)
    cache_df = load_cache(path)
    is_1h = label == "1h"

    if is_1h and not cache_df.empty and not is_valid_1h_cache(cache_df):
        print(f"⚠️ {market_arg} 1H cache is invalid or corrupted. Full cold start: {cold_period}.")
        cache_df = pd.DataFrame()

    if cache_df.empty:
        period = cold_period
    else:
        cache_age = pd.Timestamp.now(tz="UTC") - cache_df.index.max()
        if cache_age <= pd.Timedelta(minutes=tf["max_age"]):
            return cache_df, False
        period = pick_refresh_period(cache_age, cold_period)
        if period != REFRESH_PERIOD:
            print(f"ℹ️ {market_arg} {label} cache: catch-up download ({period}), age of the last candle: {cache_age}")

    fresh_df = download_in_batches(symbols, period, tf["interval"])
    if fresh_df.empty:
        return cache_df, False
    if is_1h and not is_valid_1h_cache(fresh_df, min_rows=1):
        print(f"❌ {market_arg} 1H fresh data failed the integrity check. Cache save aborted.")
        return cache_df, False

    merged = merge_and_dedupe(cache_df, fresh_df)
    if len(merged) > tf["trim"]:
        merged = merged.iloc[-tf["trim"]:]
    if is_1h and not is_valid_1h_cache(merged, min_rows=1):
        print(f"❌ {market_arg} 1H cache failed the pre-save check. Not saving.")
        return cache_df, False

    save_cache(path, merged)
    return merged, True


# ==================================================================================
# LOCKING + STATE
# ==================================================================================
def lock_file_path(market_arg):
    os.makedirs(LOCK_DIR, exist_ok=True)
    return os.path.join(LOCK_DIR, f"{market_arg}.lock")


def is_pid_running(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_lock(path):
    """True: may run. False: a previous run is still working. Releases a stuck lock (dead PID)."""
    if os.path.exists(path):
        old_pid = None
        try:
            with open(path, "r", encoding="utf-8") as f:
                old_pid = int(f.read().strip())
        except Exception:
            pass
        if old_pid is not None and is_pid_running(old_pid):
            return False
        print(f"WARNING: stale lock file ({path}), the previous run (PID {old_pid}) is no longer running. Releasing.")
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    return True


def release_lock(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"WARNING: failed to delete the lock file ({path}): {e}")


def state_file_path(market_arg):
    os.makedirs(STATE_DIR, exist_ok=True)
    return os.path.join(STATE_DIR, f"state_{market_arg}.json")


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(path, state):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)
    os.replace(tmp, path)


def is_in_alert_cooldown(symbol_state, now_utc, direction):
    """True if ALERT_COOLDOWN_MIN minutes have not yet passed in the SAME direction. False on invalid data."""
    if symbol_state.get("last_signal_direction") != direction:
        return False
    try:
        last = datetime.fromisoformat(symbol_state["last_signal_time"])
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
    except Exception:
        return False
    return (now_utc - last).total_seconds() < ALERT_COOLDOWN_MIN * 60


# ==================================================================================
# ERROR LOG + TELEGRAM
# ==================================================================================
def write_error_log(message, market_arg=None, exc=None):
    """log/error_YYYY_MM_DD.log (New York date). Never raises an exception. Does NOT go to Telegram."""
    try:
        now_ny = datetime.now(NY_TZ)
        os.makedirs(LOG_DIR, exist_ok=True)
        path = os.path.join(LOG_DIR, f"error_{now_ny.strftime('%Y_%m_%d')}.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{now_ny.strftime('%Y.%m.%d %H:%M:%S')} {market_arg or '-'} [ERROR] {message}\n")
            if exc is not None:
                f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception as e:
        print(f"WARNING: failed to write the error log: {e}")


def notify_admin(message, key="general", throttle_min=30):
    """Plain-text message ONLY to the admin. Does nothing if not configured."""
    if not TELEGRAM_ADMIN_CHAT_ID:
        return
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        marker = os.path.join(STATE_DIR, f"admin_alert_{key}.txt")
        if os.path.exists(marker) and time.time() - os.path.getmtime(marker) < throttle_min * 60:
            return
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          json={"chat_id": TELEGRAM_ADMIN_CHAT_ID, "text": message[:3500]}, timeout=10)
        if r.status_code == 200:
            with open(marker, "w", encoding="utf-8") as f:
                f.write(str(time.time()))
    except Exception as e:
        print(f"WARNING: admin notification failed: {e}")


def _record_telegram_sent():
    """Daily Telegram statistics (log/telegram_count_YYYY_MM_DD.json). Never raises an exception."""
    try:
        now = datetime.now(NY_TZ)
        path = os.path.join(LOG_DIR, f"telegram_count_{now.strftime('%Y_%m_%d')}.json")
        os.makedirs(LOG_DIR, exist_ok=True)
        stats = {"date": now.strftime("%Y-%m-%d"), "total": 0, "hourly": {}}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                stats = json.load(f)
        hour = now.strftime("%H")
        stats["total"] = stats.get("total", 0) + 1
        stats["hourly"][hour] = stats["hourly"].get(hour, 0) + 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"WARNING: failed to update the Telegram statistics: {e}")


_alert_queue = []
_queue_lock = threading.Lock()
_flusher_stop = threading.Event()
_flusher_thread = None


def enqueue_telegram_alert(text):
    with _queue_lock:
        _alert_queue.append(text)


def _pack_batches(messages):
    batches, current = [], ""
    for m in messages:
        if len(m) > TELEGRAM_MAX_LEN:
            m = m[:TELEGRAM_MAX_LEN - 3] + "..."
        candidate = m if not current else current + TELEGRAM_SEPARATOR + m
        if len(candidate) > TELEGRAM_MAX_LEN and current:
            batches.append(current)
            current = m
        else:
            current = candidate
    if current:
        batches.append(current)
    return batches


def _post_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}

    for _ in range(3):
        try:
            r = requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"❌ Telegram exception: {e}")
            return False
        if r.status_code == 200:
            return True
        try:
            data = r.json()
        except Exception:
            data = {}
        params = data.get("parameters", {})
        if r.status_code == 429:                       # rate limit
            time.sleep(int(params.get("retry_after", 5)) + 1)
            continue
        if r.status_code == 400 and "parse entities" in data.get("description", ""):
            payload.pop("parse_mode", None)            # Markdown error -> plain text
            continue
        print(f"⚠️ Telegram error ({r.status_code}): {r.text}")
        return False
    return False


def flush_telegram_queue():
    with _queue_lock:
        messages = _alert_queue[:]
        _alert_queue.clear()
    if not messages:
        return
    batches = _pack_batches(messages)
    for i, batch in enumerate(batches):
        if _post_telegram(TELEGRAM_CHAT_ID, batch):
            _record_telegram_sent()
            time.sleep(1.1)                            # <= 1 message/sec/chat
        else:
            with _queue_lock:
                _alert_queue[:0] = batches[i:]         # back to the front of the queue
            return


def start_telegram_flusher():
    global _flusher_thread
    _flusher_stop.clear()

    def loop():
        while not _flusher_stop.wait(TELEGRAM_BATCH_INTERVAL_SEC):
            flush_telegram_queue()

    _flusher_thread = threading.Thread(target=loop, daemon=True)
    _flusher_thread.start()


def stop_telegram_flusher():
    _flusher_stop.set()
    if _flusher_thread:
        _flusher_thread.join(timeout=60)
    flush_telegram_queue()                             # final flush
    with _queue_lock:
        leftover = _alert_queue[:]
        _alert_queue.clear()
    if leftover:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(OUTBOX_PATH, "w", encoding="utf-8") as f:
            json.dump(leftover, f, ensure_ascii=False)
        write_error_log(f"{len(leftover)} Telegram messages were not sent, saved to the outbox "
                        f"(the next run will try again).")


def load_outbox():
    if not os.path.exists(OUTBOX_PATH):
        return
    try:
        with open(OUTBOX_PATH, "r", encoding="utf-8") as f:
            for m in json.load(f):
                enqueue_telegram_alert(m)
        os.remove(OUTBOX_PATH)
    except Exception as e:
        print(f"WARNING: failed to load the outbox: {e}")


# ==================================================================================
# SCANNER
# ==================================================================================
def build_final_list(watchlist_by_suffix):
    """{suffix: [tickers]} -> Yahoo symbols, without duplicates (no suffix for USA)."""
    final, seen = [], set()
    for suffix, tickers in watchlist_by_suffix.items():
        for ticker in tickers:
            symbol = str(ticker) if suffix == "USA" else f"{ticker}.{suffix}"
            if symbol not in seen:
                seen.add(symbol)
                final.append(symbol)
    return final


def fmt_price(value, currency):
    return f"{value:.2f} {currency}"


OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def analyze_symbol(symbol, arg, run, data_5m, data_15m, data_1h, state):
    """Evaluates one symbol. Returns: (ok, data)
       ok == "signal"  -> data = {"text": Telegram text, "state": new state, "log": console line}
       otherwise       -> ok is the reason for skipping (the key of the daily log counter)."""
    ex = exchange_of(symbol)
    if ex is None:
        return "unknown_suffix", None

    raw_5m, raw_15m, raw_1h = (d[symbol][OHLCV] for d in (data_5m, data_15m, data_1h))

    # GAP check on the raw data, BEFORE dropna()
    for raw, tf in ((raw_5m, TF_5M), (raw_15m, TF_15M), (raw_1h, TF_1H)):
        warn_on_unexpected_gap(raw, tf["minutes"], symbol, ex)

    df_5m, df_15m, df_1h = raw_5m.dropna(), raw_15m.dropna(), raw_1h.dropna()
    if df_5m.empty or df_15m.empty or df_1h.empty:
        return "no_data", None

    df_5m = filter_to_market_sessions(drop_unclosed_candle(df_5m, TF_5M["minutes"]), ex)
    df_15m = drop_unclosed_candle(df_15m, TF_15M["minutes"])
    df_4h = resample_to_4h(drop_unclosed_candle(df_1h, TF_1H["minutes"]), ex)

    if len(df_5m) < WARMUP_BARS or len(df_15m) < WARMUP_BARS or len(df_4h) < WARMUP_BARS:
        return "warmup", None

    # Fresh-candle protection
    bar_close = df_5m.index[-1] + pd.Timedelta(minutes=TF_5M["minutes"])
    if (pd.Timestamp.now(tz="UTC") - bar_close).total_seconds() / 60.0 > MAX_SIGNAL_BAR_AGE_MIN:
        return "stale_candle", None

    # --- 4H context ---
    rsi_4h_s = compute_rsi(df_4h["Close"], RSI_PERIOD)
    adx_s, plus_di_s, minus_di_s = compute_adx(df_4h["High"], df_4h["Low"], df_4h["Close"], ADX_PERIOD)
    values = (rsi_4h_s.iloc[-1], adx_s.iloc[-1], plus_di_s.iloc[-1], minus_di_s.iloc[-1])
    if any(pd.isna(v) for v in values):
        return "missing_value", None
    rsi_4h, adx_4h, plus_di, minus_di = (float(v) for v in values)

    if rsi_4h > RSI_4H_LONG_MIN:
        trend = "BULLISH"
    elif rsi_4h < RSI_4H_SHORT_MAX:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"
    strong_against = {   # a strong 4H trend that a reversal in the given direction goes against
        "LONG": trend == "BEARISH" and adx_4h >= ADX_4H_MIN and minus_di > plus_di,
        "SHORT": trend == "BULLISH" and adx_4h >= ADX_4H_MIN and plus_di > minus_di,
    }

    # --- 5M ---
    rsi_5m_s = compute_rsi(df_5m["Close"], RSI_PERIOD)
    rvol_s = compute_relative_volume(df_5m["Volume"], REVERSAL_RVOL_PERIOD)
    vwap_s = compute_session_vwap(df_5m, ex)
    if pd.isna(rsi_5m_s.iloc[-1]) or pd.isna(vwap_s.iloc[-1]):
        return "missing_value", None
    rsi_5m, vwap = float(rsi_5m_s.iloc[-1]), float(vwap_s.iloc[-1])
    price = float(df_5m["Close"].iloc[-1])
    rvol_last = 0.0 if pd.isna(rvol_s.iloc[-1]) else float(rvol_s.iloc[-1])

    feat = compute_features(df_5m, rvol_s, rsi_5m_s)
    candidates = []
    for direction in ("LONG", "SHORT"):
        if is_valid_reversal_setup(direction, feat):
            score = calculate_reversal_score(direction, feat, price, vwap, trend)
            if score >= REVERSAL_SCORE_MIN:
                candidates.append((direction, score))
    if not candidates:
        return "no_signal", None
    direction, score = max(candidates, key=lambda x: x[1])

    if strong_against[direction] and score < REVERSAL_SCORE_STRONG_AGAINST_TREND:
        return "trend_filter", None

    # --- duplicate + cooldown ---
    signal_bar = str(df_5m.index[-1])
    prev = state.get(symbol, {})
    if prev.get("last_signal_bar") == signal_bar and prev.get("last_signal_direction") == direction:
        return "duplicate", None
    if is_in_alert_cooldown(prev, datetime.now(timezone.utc), direction):
        return "cooldown", None

    # --- 15M ATR (SL/TP) + BB width (info) ---
    atr = compute_atr(df_15m["High"], df_15m["Low"], df_15m["Close"], ATR_PERIOD).iloc[-1]
    bb_width = compute_bollinger_width(df_15m["Close"], BB_PERIOD, BB_STD).iloc[-1]
    if pd.isna(atr) or pd.isna(bb_width):
        print(f"⚠️ {symbol}: 15M ATR/Bollinger missing, signal skipped (score={score}, {direction})")
        return "missing_value", None
    atr, bb_width = float(atr), float(bb_width)

    # --- Telegram text ---
    currency = ex["currency"]
    ticker_line = symbol
    label = run["label"]
    if direction == "LONG":
        title = f"🟢 *EARLY REVERSAL LONG ({label})*"
        status = "🟢 EARLY REVERSAL LONG"
        price_lines = [
            f"*Entry price:* {fmt_price(price, currency)}",
            f"*Stop-loss:* {fmt_price(price - SL_ATR_MULT * atr, currency)}",
            f"*Take-profit:* {fmt_price(price + TP_ATR_MULT * atr, currency)}",
        ]
    else:   # CASH ACCOUNT: no short SL/TP on a bearish signal
        title = f"🔴 *SELL WARNING / BEARISH REVERSAL ({label})*"
        status = "🔴 SELL WARNING / BEARISH REVERSAL"
        price_lines = [f"*Current price:* {fmt_price(price, currency)}"]

    text = "\n".join([
        title, "",
        f"*Ticker:* {ticker_line}",
        f"*4H context:* {trend}",
        f"*4H RSI / ADX:* {rsi_4h:.1f} / {adx_4h:.1f}",
        f"*5M RSI:* {rsi_5m:.1f}",
        f"*5M VWAP:* {fmt_price(vwap, currency)}",
        f"*5M RVOL:* {rvol_last:.2f}x",
        f"*Reversal score:* {score}",
        f"*BB width (15M):* {bb_width:.2f}%",
        *price_lines,
        f"*Status:* {status}",
        f"*Time (New York):* {datetime.now(NY_TZ).strftime('%H:%M')}",
    ])
    return "signal", {
        "text": text,
        "state": {
            "last_signal_bar": signal_bar,
            "last_signal_direction": direction,
            "last_signal_time": datetime.now(timezone.utc).isoformat(),
            "last_reversal_score": score,
        },
        "log": f"Alert sent: {symbol} | {direction} | score={score} | RVOL={rvol_last:.2f}",
    }


def run_scan():
    run_start = datetime.now(NY_TZ)      # on error we write THIS to the log (the scheduled start)

    if len(sys.argv) < 2:
        write_log_line("unknown", "error: no market argument provided", run_start)
        raise ValueError(f"No market specified. Usage: RSI_search.py {' | '.join(RUNS)}")
    arg = sys.argv[1].lower()
    if arg not in RUNS:
        write_log_line(arg, "error: invalid market argument", run_start)
        raise ValueError(f"Invalid market: '{arg}'. Valid values: {', '.join(RUNS)}")

    run = RUNS[arg]
    market_name = run["label"]
    symbols = build_final_list(getattr(watchlists, f"{run['watchlist']}_watchlist_by_suffix"))
    stamp = run_start.strftime("%Y-%m-%d %H:%M:%S")

    if not symbols:
        print(f"[{stamp}] {market_name} watchlist is empty, skipped.")
        write_log_line(arg, "error: watchlist is empty", run_start)
        return

    lock_path = lock_file_path(arg)
    if not acquire_lock(lock_path):
        print(f"[{stamp}] {market_name}: the previous run is still working, this run is skipped.")
        write_log_line(arg, "error: locked, previous run still working", run_start)
        return

    state_path = state_file_path(arg)
    state = {}
    state_dirty = False
    try:
        print(f"[{stamp}] Current market: {market_name}. Checking {len(symbols)} stocks...")
        state = load_state(state_path)
        load_outbox()
        start_telegram_flusher()

        data_5m, ref_5m = get_or_refresh_cache(arg, "5m", symbols, TF_5M)
        data_15m, ref_15m = get_or_refresh_cache(arg, "15m", symbols, TF_15M)
        data_1h, ref_1h = get_or_refresh_cache(arg, "1h", symbols, TF_1H,
                                               COLD_PERIOD_1H_OVERRIDE.get(arg))

        if data_5m.empty or data_15m.empty or data_1h.empty:
            write_error_log(f"{market_name}: failed to download data (one of 5M/15M/1H is empty)", arg)
            notify_admin(f"⚠️ RSI SCANNER: {arg}: failed to download data (Yahoo?).", key=f"download_{arg}")
            print("Failed to download data.")
            write_log_line(arg, "error: failed to download data", run_start)
            return

        refreshed = [name for name, flag in (("5M", ref_5m), ("15M", ref_15m), ("4H", ref_1h)) if flag]

        # Handling missing symbols: only the symbols present in all three tables
        available = (set(data_5m.columns.get_level_values(0))
                     & set(data_15m.columns.get_level_values(0))
                     & set(data_1h.columns.get_level_values(0)))

        skip = dict.fromkeys(
            ["no_data", "unknown_suffix", "warmup", "stale_candle", "no_signal", "trend_filter",
             "duplicate", "cooldown", "missing_value", "error", "signal"], 0)
        errors_logged = 0
        MAX_SYMBOL_ERRORS_LOGGED = 3

        for symbol in symbols:
            if symbol not in available:
                skip["no_data"] += 1
                continue
            try:
                outcome, result = analyze_symbol(symbol, arg, run, data_5m, data_15m, data_1h, state)
            except Exception as e:
                skip["error"] += 1
                print(f"⚠️ {symbol}: {e}")
                if errors_logged < MAX_SYMBOL_ERRORS_LOGGED:   # under cron the console output is lost
                    errors_logged += 1
                    write_error_log(f"{symbol}: {type(e).__name__}: {e}", arg, exc=e)
                continue

            skip[outcome] += 1
            if outcome == "signal":
                enqueue_telegram_alert(result["text"])
                state[symbol] = result["state"]
                state_dirty = True
                print(result["log"])

        summary = [f"{k}={v}" for k, v in skip.items() if v > 0]
        print(f"Summary ({arg}): " + (", ".join(summary) if summary else "-"))
        write_log_line(arg, ", ".join(refreshed + summary) if (refreshed or summary) else "-")

    finally:
        if state_dirty:
            save_state(state_path, state)
        stop_telegram_flusher()
        release_lock(lock_path)


if __name__ == "__main__":
    try:
        run_scan()
    except Exception as e:
        # goes to the error log (log/error_*.log), NOT to Telegram; the exit code stays non-zero.
        market_for_log = sys.argv[1].lower() if len(sys.argv) > 1 else None
        write_error_log("CRITICAL error in the scanner", market_for_log, exc=e)
        notify_admin(f"⚠️ RSI SCANNER CRITICAL error ({market_for_log or '-'}): {type(e).__name__}: {e}",
                     key=f"critical_{market_for_log or 'x'}")
        raise
