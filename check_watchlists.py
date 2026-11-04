#!/usr/bin/env python3
"""Watchlist checker: run after every watchlists.py change:  python check_watchlists.py
Checks: syntax, whether every RUNS market has a list, whether the suffixes match the exchange,
duplicate tickers, empty lists, and whether the trailing comment count matches the ticker count.
Optional:  python check_watchlists.py --yahoo   (approx. 1-2 minutes) -> also checks whether Yahoo accepts
the tickers in the form the scanner requests them (5-minute data); for the failing ones it suggests another suffix."""
import re
import sys

from markets import RUNS, SUFFIX_MAP

errors = warnings = 0


def err(msg):
    global errors
    errors += 1
    print(f"❌ {msg}")


def warn(msg):
    global warnings
    warnings += 1
    print(f"⚠️  {msg}")


try:
    import watchlists
except SyntaxError as e:
    print(f"❌ watchlists.py SYNTAX ERROR: {e.msg} (line {e.lineno})")
    print(f"   -> {(e.text or '').strip()[:100]}")
    print("   Tip: don't put the closing } after a # comment.")
    sys.exit(1)

used = set()
for key, run in RUNS.items():
    name = f"{run['watchlist']}_watchlist_by_suffix"
    used.add(name)
    wl = getattr(watchlists, name, None)
    if wl is None:
        err(f"{key}: watchlists.{name} is missing")
        continue
    total = sum(len(v) for v in wl.values())
    if total == 0:
        warn(f"{key}: empty watchlist (the scheduler will skip it)")
    for suffix, tickers in wl.items():
        if suffix != "USA" and SUFFIX_MAP.get(suffix) != run["exchange"]:
            err(f"{key}: the '{suffix}' suffix does not belong to the {run['exchange']} exchange")
        dups = sorted({t for t in tickers if tickers.count(t) > 1})
        if dups:
            err(f"{key}/{suffix}: duplicate ticker: {dups}")
        bad = [t for t in tickers if not isinstance(t, str) or not t.strip() or " " in t]
        if bad:
            err(f"{key}/{suffix}: invalid ticker: {bad}")

for name in dir(watchlists):
    if name.endswith("_watchlist_by_suffix") and name not in used:
        warn(f"{name}: no matching market in RUNS (typo?)")

# comment-count check (trailing '# ... N (xx%)' vs. the actual number of tickers on the line)
with open(watchlists.__file__, encoding="utf-8") as f:
    for n, line in enumerate(f, 1):
        if line.lstrip().startswith("#"):
            continue
        m = re.search(r'"(\w+)":\s*\[(.*?)\]', line)
        c = re.search(r'#.*?\b(\d+)\s*\(', line)
        if m and c:
            real = len(re.findall(r'"[^"]+"', m.group(2)))
            if real != int(c.group(1)):
                warn(f"line {n} ({m.group(1)}): the comment says {c.group(1)} tickers, but the list contains {real}")


# ---- optional: does Yahoo accept the tickers ------------------------------------
YAHOO_BATCH = 250      # number of tickers requested at once
YAHOO_PAUSE = 5        # seconds to pause between two batches (Yahoo rate-limit protection)
ALT_SUFFIX = {"TW": ["TWO"], "TWO": ["TW"], "KS": ["KQ"], "KQ": ["KS"], "TO": ["V", "CN"]}


def check_yahoo():
    import time

    import yfinance as yf
    from yfinance import shared

    sym_market = {}
    for key, run in RUNS.items():
        wl = getattr(watchlists, f"{run['watchlist']}_watchlist_by_suffix", {})
        for suffix, tickers in wl.items():
            for t in tickers:
                sym_market.setdefault(str(t) if suffix == "USA" else f"{t}.{suffix}", key)
    symbols = list(sym_market)
    print(f"\nYahoo check: {len(symbols)} tickers (5-minute data, same as the scanner uses)...")

    bad = {}
    for i in range(0, len(symbols), YAHOO_BATCH):
        part = symbols[i:i + YAHOO_BATCH]
        shared._ERRORS.clear()
        got = set()
        try:
            df = yf.download(part, period="5d", interval="5m", group_by="ticker",
                             progress=False, threads=True)
            if df is not None and not df.empty:
                if hasattr(df.columns, "levels"):
                    present = set(df.columns.get_level_values(0))
                    got = {s for s in part if s in present and df[s]["Close"].notna().any()}
                elif df["Close"].notna().any():
                    got = set(part)
        except Exception as e:
            print(f"   batch {i // YAHOO_BATCH + 1}: exception: {type(e).__name__}: {e}")
        errs = dict(shared._ERRORS)
        for s in part:
            if s not in got:
                bad[s] = str(errs.get(s, "no data")).strip()[:60]
        if i + YAHOO_BATCH < len(symbols):
            time.sleep(YAHOO_PAUSE)

    # look for an alternative suffix for the failing tickers (daily data is enough for the test)
    hint = {}
    for s, reason in bad.items():
        if "." not in s or "tradingPeriods" in reason:
            continue
        base, suf = s.rsplit(".", 1)
        for alt in ALT_SUFFIX.get(suf.upper(), []):
            cand = f"{base}.{alt}"
            time.sleep(0.5)
            try:
                d = yf.download(cand, period="1mo", interval="1d", progress=False)
            except Exception:
                continue
            if d is not None and not d.empty:
                hint.setdefault(s, []).append(cand)

    if not bad:
        print("✅ Yahoo accepted all %d tickers." % len(symbols))
        return
    by_market = {}
    for s in bad:
        by_market.setdefault(sym_market[s], []).append(s)
    for market, items in by_market.items():
        warn(f"{market}: {len(items)} tickers could not be retrieved from Yahoo")
        for s in items:
            extra = f"  -> maybe: {', '.join(hint[s])}" if s in hint else ""
            print(f"      {s:12s} {bad[s]}{extra}")
    print(f"\nTotal: {len(bad)}/{len(symbols)} tickers failed. (On weekends, intraday data may be missing for some markets;"
          f" for a final verdict, it's worth running this on a weekday as well.)")


if "--yahoo" in sys.argv:
    check_yahoo()

print(f"\nDone: {errors} errors, {warnings} warnings.")
sys.exit(1 if errors else 0)
