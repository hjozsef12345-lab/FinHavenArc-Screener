# FinHavenArc-Screener

A free, self-hosted stock screener that sends early-reversal alerts to your own Telegram chat.

It watches 1,076 tickers on 28 markets (US, Canada, Brazil, Mexico, Europe, Asia-Pacific) during their local trading hours, scans each market every 5 minutes, and messages you only when its rules find a possible reversal. No subscription, no accounts, no telemetry.

Example Telegram alert

<!-- Replace with a real screenshot of a Telegram alert (blur nothing sensitive: no token, no chat ID). -->

Not financial advice. This is a monitoring tool that applies fixed mechanical rules to free market data. It does not trade, does not know your account, and has not been backtested. Every decision and every risk is yours.

Why self-hosted
Private. Alerts go only to the chat ID you set. Nobody else sees what you follow.
No black box. The full source is here and every scoring rule is documented, so you can see exactly why an alert fired.
Yours to tune. Watchlists are plain text. Thresholds, stop/target multipliers and cooldowns are named settings.
No dependency on me. It talks only to Yahoo Finance and Telegram. If my website disappears, your screener keeps running.
No cost beyond a server. Free data (via yfinance), free Telegram bot.

The trade-off: you need a small Linux server and a little comfort with the terminal.

What it does

Every 5 minutes, per market, while the exchange is open:

Downloads 5-minute, 15-minute and 1-hour data from Yahoo Finance (cached, refreshed by age).
Evaluates the last closed 5-minute candle (closed candles only, to avoid look-ahead bias) using price structure, volume, VWAP and RSI, with the 4-hour trend (built from hourly data) as context.
Sends a Telegram alert if a valid setup reaches the score threshold.
Alert	Meaning
🟢 EARLY REVERSAL LONG	Price may be turning up. Shows Entry / Stop-loss / Take-profit reference levels (ATR-based).
🔴 SELL WARNING / BEARISH REVERSAL	Price may be turning down. If you hold the stock, you may want to review it. Not a short signal.

Alerts generated within the same few seconds are batched into one message, so your phone does not buzz for every signal.

Signal logic in brief
A direction is a candidate only if RVOL ≥ 1.30, there is at least one price-action event (failed breakdown/breakout, higher low/lower high, rejection candle) and at least one confirmation (strong close, volume pressure, RSI turn).
A 14-point score adds VWAP reclaim/rejection and 4H alignment. Threshold: 6, or 8 against a strong 4H trend (ADX ≥ 20).
Duplicate protection per candle, and a 60-minute same-direction cooldown per stock.
Stop-loss = Entry − 4 × ATR(14, 15M); Take-profit = Entry + 8 × ATR(14, 15M).

The complete rule set is in the guide.

Design around free data

Free Yahoo data gets throttled, so the whole system is built around its limits:

batches of at most 250 tickers, with a pause of at least 5 seconds between batches;
every scan must finish within 5 minutes (scanner runs are stopped at 295 s);
a cap of 500 tickers per region (the "2 × 250 rule").

Other implementation notes:

Per-exchange scheduling in local time with exchange_calendars (DST and holidays handled; lunch breaks in Tokyo, Hong Kong and China).
Age-based cache with catch-up logic after weekends, holidays or downtime.
4H candles built from 1H data by counting trading minutes from the open.
Queue-based Telegram sender with batching, HTTP 429 handling, plain-text fallback and an outbox for failed messages.
A cron + flock watchdog guarantees exactly one scheduler and restarts it if it stops.
Requirements
Linux with cron and flock (a small VPS is ideal; home server or Raspberry Pi also works if it runs 24/7)
Python 3.10+
1 vCPU / 1 GB RAM / 2 GB disk minimum (2 vCPU / 2 GB / 5 GB recommended)
Outbound HTTPS only. No web server, database or open inbound port.
A Telegram account and a free bot from @BotFather

Windows and macOS are not supported out of the box (the scheduler uses venv/bin/python and flock). Use a Linux server or WSL.

Quick start
bash
mkdir -p ~/rsi-scanner && cd ~/rsi-scanner
# copy the project files here, then:
python3 -m venv venv
venv/bin/pip install yfinance pandas numpy requests exchange_calendars tzdata
mkdir -p cache state lock log
Create your bot with @BotFather, press Start on it, and find your chat ID.
Create secrets.env containing one line, then protect it:
   TELEGRAM_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
bash
   chmod 600 secrets.env
Put your chat ID in RSI_search.py:
python
   TELEGRAM_CHAT_ID = ("123456789")
Check the watchlists and run one market by hand:
bash
   venv/bin/python check_watchlists.py
   venv/bin/python RSI_search.py japan
Add the watchdog to cron (one line, absolute paths):
   * * * * * /usr/bin/flock -n /home/USER/rsi-scanner/scheduler.flock /home/USER/rsi-scanner/venv/bin/python /home/USER/rsi-scanner/scheduler.py >> /home/USER/rsi-scanner/log/scheduler.out 2>&1

The full step-by-step guide (Telegram setup, pre-warming, systemd alternative, maintenance, troubleshooting, security) is here: **[Full installation guide](https://finhavenarc.com/free-stock-screener-telegram-alerts-self-hosted/)**

Files
File	Purpose
RSI_search.py	Scanner: evaluates one market, sends alerts, exits. Holds your chat ID.
scheduler.py	Runs continuously and starts the scanner for every market when due.
markets.py	Exchanges, sessions, time zones, suffixes and runnable markets.
watchlists.py	The watched tickers, grouped by market and Yahoo suffix.
check_watchlists.py	Validates watchlists.py (add --yahoo to test every ticker against Yahoo).
LICENSE.md	MIT License plus additional notices.

secrets.env is deliberately not included. You create it with your own bot token.

Configuration

Watchlists are plain Python dictionaries:

python
japan_watchlist_by_suffix = {
    "T": ["9984", "5802", "6723"],}   # Japan (Tokyo) 3 (35%)

Main settings live at the top of RSI_search.py: REVERSAL_SCORE_MIN, REVERSAL_RVOL_MIN, ALERT_COOLDOWN_MIN, SL_ATR_MULT, TP_ATR_MULT, and others. Want warnings only for your own holdings? Replace a list with just your tickers.

Limitations (please read)
No backtesting. Thresholds are settings, not proven optimized values. The engine is tuned for early signals and accepts a fair amount of noise.
Yahoo data can be late (15–30 minutes or more on some exchanges), incomplete or missing, and its volume can differ from your broker's. RVOL is only meaningful relative to Yahoo's own data.
Yahoo's free data is generally meant for personal, non-commercial use. This license gives you no rights to Yahoo data; check their terms.
No scans in the first 5 and last 15 minutes of each session.
Early closes are not known to the scheduler (stale-data protection filters them).
Alerts do not account for commissions, spreads or currency risk.
Your screener is only as available as your server, connection, Yahoo and Telegram. Verify prices in your broker or charting platform before acting.
Feedback welcome

I would especially like feedback on the signal logic (volume normalization, validation approaches) and on the Yahoo rate-limit handling. Issues and pull requests are welcome.

Questions about installation and usage: support@finhavenarc.com (free, best effort).

License

MIT License plus additional notices. See LICENSE.md; only the full text is legally binding. The software is provided "as is", without warranty. The name "FinHavenArc" is not licensed as a trademark; if you distribute a modified version, please say that it is modified.

Author

Jozsef Huszar, [FinHavenArc](https://finhavenarc.com/free-stock-screener-telegram-alerts-self-hosted/)
