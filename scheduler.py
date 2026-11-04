#!/usr/bin/env python3
import importlib
import os
import subprocess
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import watchlists
from markets import (BASE_DIR, CLOSE_DELAY, EXCHANGES, OPEN_DELAY, RUNS, WEEKDAYS,
                    run_sessions, write_log_line)

SCANNER_FILE = os.path.join(BASE_DIR, "RSI_search.py")
PYTHON_BIN = os.path.join(BASE_DIR, "venv", "bin", "python")
CHECK_INTERVAL = 10      # seconds
SCANNER_TIMEOUT = 295    # seconds
SLOW_RUN_SEC = 120       # runs slower than this get written to the log

_calendars = {}
_warned = set()


def is_trading_day(code, day):
    """Holiday filtering with exchange_calendars. If the package is missing or fails,
    returns True (the scanner's fresh-candle protection skips stale data anyway)."""
    if not code:
        return True
    try:
        if code not in _calendars:
            import exchange_calendars as xcals
            _calendars[code] = xcals.get_calendar(code)
        return bool(_calendars[code].is_session(day.isoformat()))
    except Exception as e:
        if code not in _warned:
            _warned.add(code)
            print(f"WARNING: {code} calendar unavailable ({e}), holiday filtering skipped.")
        return True


def watchlist_size(run):
    name = f"{run['watchlist']}_watchlist_by_suffix"
    wl = getattr(watchlists, name, None)
    if wl is None and name not in _warned:
        _warned.add(name)
        print(f"WARNING: watchlists.{name} is missing, the market is skipped.")
    return sum(len(v) for v in wl.values()) if wl else 0


_last_reload = 0


def active_markets():
    """The markets to run: skips those with an empty (or missing) watchlist. Reloads
    watchlists.py every minute, so a change takes effect without restarting the scheduler;
    on a syntax error the old state is kept."""
    global _last_reload
    if time.time() - _last_reload > 60:
        _last_reload = time.time()
        try:
            importlib.reload(watchlists)
        except Exception as e:
            print(f"WARNING: failed to reload watchlists.py ({e}), keeping the old one.")
    return {m: r for m, r in RUNS.items() if watchlist_size(r) > 0}


def due_key(run, now_utc):
    """If the market must run in the CURRENT 5-minute slot, returns a unique key
    (unique per slot), otherwise None.

    The decision is based on the slot, not on the exact minute: when earlier markets
    in the sequential loop take long (e.g. Europe ~70 s, US 130-250 s), a market that
    gets its turn at :x1 or :x2 still runs for the :x0 slot instead of being skipped.
    last_key in main() guarantees that each market runs only once per slot.
    """
    local = now_utc.astimezone(ZoneInfo(EXCHANGES[run["exchange"]]["tz"]))
    if local.isoweekday() not in WEEKDAYS:
        return None
    minute = local.hour * 60 + local.minute
    slot = minute - minute % 5          # start of the current 5-minute slot
    for start, end in run_sessions(run):
        if start + OPEN_DELAY <= slot <= end - CLOSE_DELAY:
            if is_trading_day(run.get("calendar"), local.date()):
                return f"{local:%Y-%m-%d}-{slot}"
            return None
    return None

def run_scanner(market):
    if not os.path.exists(SCANNER_FILE) or not os.path.exists(PYTHON_BIN):
        print("ERROR: The scanner or the venv is missing.")
        return
    print(f"\n[{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC] Starting: {market}")
    started = time.time()
    try:
        env = dict(os.environ, RSI_RUN_SOURCE="scheduler")
        result = subprocess.run([PYTHON_BIN, SCANNER_FILE, market], cwd=BASE_DIR,
                                env=env, timeout=SCANNER_TIMEOUT)
        if result.returncode != 0:
            write_log_line(market, f"ERROR: Exit code: {result.returncode}")
        elapsed = time.time() - started
        if elapsed > SLOW_RUN_SEC:
            write_log_line(market, f"SLOW run: {elapsed:.0f} s")
    except Exception as e:
        write_log_line(market, f"ERROR: {e}")


def main():
    print("==============================================")
    print(" RSI Scanner Scheduler started")
    print(f" Markets:        {', '.join(active_markets())}")
    print(f" Check interval: {CHECK_INTERVAL} seconds")
    print("==============================================")

    last_key = {}
    while True:
        try:
            for market, run in active_markets().items():
                key = due_key(run, datetime.now(timezone.utc))
                if key is None or last_key.get(market) == key:
                    continue
                last_key[market] = key
                run_scanner(market)
        except Exception as e:
            print(f"SCHEDULER ERROR: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
