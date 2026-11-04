# FinHavenArc Screener: User and Operator Guide

*Informational purposes only, not financial advice. Always do your own research. See our Financial Disclaimer for details.*

A free, open-source, self-hosted stock screener that sends early-reversal alerts to your own Telegram chat. Documentation release: October 2026.

**Download.** Thank you for your interest in FinHavenArc Screener, a free, open-source tool. Please download the package only from the official page, and review the Software License before you install or use the software.

> By downloading, you agree to the [Software License](#) and acknowledge the [Privacy Policy](#).

**Not financial advice.** The screener is a free, automated tool that applies a fixed set of mechanical rules to market data. It does not know your account, your goals, or your risk tolerance. Every decision, and every risk, is yours.

**No guarantee of availability or data quality.** The screener depends on free third-party data (Yahoo Finance), on Telegram, and on a server that you run. Data can arrive late, be incomplete, or be missing. Servers and services can go down. The system has been stable in my experience, but I cannot promise that it will never fail. Please read section 4.3.

---

## Contents

**Part 1: Introduction**
1.1 Why I built this screener · 1.2 What you get · 1.3 Why a free, self-hosted screener is better · 1.4 Free data, and the rules that keep it free · 1.5 How the stocks were chosen · 1.6 At a glance

**Part 2: User guide**
2.1 What is the screener for? · 2.2 Markets and schedule · 2.3 How a signal is decided · 2.4 Alert fields and delivery · 2.5 Data and reliability · 2.6 Frequently asked questions · 2.7 Limitations and important notes · 2.8 Glossary

**Part 3: Operator guide (installing and running it)**
3.1 Architecture and files · 3.2 What you need · 3.3 Installation step by step · 3.4 Telegram setup · 3.5 The secrets.env file · 3.6 Pre-flight check, first test run, and pre-warming · 3.7 Running it around the clock · 3.8 Stopping, restarting, and updating · 3.9 Configuration reference · 3.10 The watchlist checker · 3.11 Routine maintenance · 3.12 Logging and monitoring · 3.13 Troubleshooting · 3.14 Security and privacy · 3.15 Uninstalling

**Part 4: Support, custom work, and legal**
4.1 Free support · 4.2 Custom work · 4.3 Important disclaimer: availability and data · 4.4 License

**Appendices**
A. What changed since the previous guide · B. Quick-start checklist

---

# Part 1: Introduction

## 1.1 Why I built this screener

I follow a lot of stocks and markets. After a while I started to wish for an assistant that watches them around the clock and sends me a message only when I need to step in. This screener is that assistant, and I now make it available to everyone for free, for beginner and advanced traders alike.

The technical side was easy to solve, because I run my own website on a powerful server that I was barely using. I did not understand every detail of how it would work at the beginning, but the system kept getting better, and within the limits of free data I ended up with a genuinely useful stock screener.

## 1.2 What you get

The official name of the program is FinHavenArc Screener. It is free to download, and it comes with every file needed to run it, with one deliberate exception: `secrets.env`, which holds your personal Telegram bot token. Everyone creates that file when setting up their own Telegram bot (sections 3.4 and 3.5), so it is never part of the download. Your personal chat ID, however, is set in the `RSI_search.py` file, on this line (section 3.4 explains how to find your chat ID):

```python
TELEGRAM_CHAT_ID = ("123456789")     # your personal chat ID
```

| File or folder | Included in the download? | Purpose |
|---|---|---|
| `RSI_search.py` | Yes | The scanner: evaluates one market, sends alerts, then exits. You enter your chat ID in this file (section 3.4). |
| `scheduler.py` | Yes | The scheduler: runs continuously and starts the scanner for every market when it is due. |
| `markets.py` | Yes | The single place where exchanges, sessions, time zones, suffixes, and runnable markets are defined. |
| `watchlists.py` | Yes | The watched tickers, grouped by market and exchange suffix. |
| `check_watchlists.py` | Yes | A checker that you run after every change to `watchlists.py`. |
| `LICENSE.md` | Yes | The software license (MIT License plus additional notices). |
| This guide | Yes | Everything about using and operating the screener. |
| `secrets.env` | No, you create it | Your Telegram bot token. |
| `venv/` | No, you create it | The Python environment (section 3.3). |
| `cache/`, `state/`, `lock/`, `log/` | No, created automatically | Downloaded data, per-market alert state, lock files, and logs. |

The scanner file keeps the name it had in earlier versions, `RSI_search.py` (see Appendix A).

## 1.3 Why a free, self-hosted screener is better

You download the screener and run it on your own server. Alerts go to your own Telegram bot and your own chat. Compared with a shared channel or a paid alert service, this has real advantages:

- **Your alerts are private.** The screener sends messages only to the chat ID that you set. Nobody else sees what you follow, and nobody else sees your alerts.
- **Your SELL WARNINGs become relevant.** The system does not know what you own, so it warns about every ticker on the list. If you keep your own holdings on your watchlist, a SELL WARNING means something about your positions.
- **Your own tickers, your own markets.** The lists are plain text in `watchlists.py`. You can add, remove, or replace tickers, or switch a market on or off, in minutes.
- **No subscription and no per-alert fees.** The software is free. The data is free. Telegram is free. Your only cost is the server you run it on.
- **Independence.** Your installation does not depend on my server, my availability, or my continued interest. If my website goes offline tomorrow, your screener keeps running.
- **Full transparency.** The complete source code is included in readable form, and every rule is documented in Part 2. There is no black box. You can see exactly why an alert was sent.
- **Your own tuning.** Thresholds, stop-loss and take-profit multipliers, and cooldowns are named settings at the top of the code (section 3.9).
- **Your own data budget.** Each installation talks to Yahoo from its own server. A single central service that feeds many users through one connection would be a single point of failure and a single throttling risk.
- **No accounts, no data collection.** You never register with me. The software has no telemetry. It talks only to Yahoo Finance and Telegram.

**Honest trade-offs.** Self-hosting means you need a suitable server and a little technical comfort. You are responsible for keeping it running, for updating the Python packages when Yahoo changes something, and for reviewing your watchlists. Part 3 walks you through all of it, and section 4.1 explains the free help that I offer.

## 1.4 Free data, and the rules that keep it free

Paid data providers charge a lot for the data and API calls that a serious, thorough screener needs. I did not want to pay for them, but I still needed enough stocks and enough data. Yahoo Finance makes market data available for free (through the yfinance library). Because free access can lead to throttling or a temporary IP ban if you ask for too much, I had to set a few rules. These rules apply to your installation too, because your server asks Yahoo for the data from your own IP address.

- Batches of at most 250 tickers per request.
- A pause of at least 5 seconds between batches.
- Every scan must finish within 5 minutes. The screener uses 5-minute, 15-minute, and 1-hour data. The 5-minute data is refreshed on every run, the 15-minute data about every 15 minutes, and the 1-hour data about once an hour. The top of each hour is therefore the heaviest moment, because all three timeframes are downloaded in the same run.
- **The 2 × 250 rule:** a cap of 500 tickers per region (Asia-Pacific, Europe, the Americas), counted across the markets of that region. That is the most the hourly peak can handle inside the 5-minute window. If you edit the lists, respect this cap (section 3.9).

For a free setup, refreshing 500 stocks every 5 minutes is an excellent result. It also means I had to pick the best stocks I could find.

- **The shipped lists are reviewed from time to time.** As my time allows, I review them and may publish an updated package. This is a possibility, not a promise or a guarantee, and updates can be delayed or may not come at all. If you download a newer package, compare its `watchlists.py` with yours before you overwrite anything (section 3.8).
- **Ticker codes change.** Yahoo occasionally changes them, and because the service is free this cannot be automated, so they have to be corrected by hand. `check_watchlists.py --yahoo` helps you find the broken ones (section 3.10).
- At the time of this release, all 1,076 tickers in the system passed the Yahoo check. I could easily cover 4,000–5,000, but the rate limit holds the system back. Given that limit, I am glad to be able to watch this many tickers and send alerts for them.
- **Ongoing upkeep:** updating exchange calendars, error handling, and automatic restart of the workflow (the cron watchdog in section 3.7).

All of this is a lot of work, but it lets me offer the screener at no cost.

## 1.5 How the stocks were chosen

These are my personal selection criteria and market views as of October 2026. They are not recommendations, and markets change month by month.

### Coverage

| Region | Tickers | Details |
|---|---|---|
| Americas | 459 | United States 400, Canada 34, Brazil 16, Mexico 9 |
| Asia-Pacific | 481 | Hong Kong 155, China 117, South Korea 82, Japan 72, Taiwan 30, Australia 25 |
| Europe and nearby | 136 | Many countries share these slots. The United Kingdom (32), Germany (20), and France and Turkey (19 each) lead. |

The United States is the priority, with 400 stocks. 310 of them run alongside the European markets for about two hours, which is the overlap in trading hours. The 90 smallest U.S. companies therefore start two hours later (at 11:30 New York time), when most European exchanges have closed. If demand grows, this is easy to adjust: all 400 U.S. stocks could run from the open, and Europe, with its 136 stocks, would simply finish its run two hours earlier.

Canada, Mexico, and Brazil also have a place in the Americas.

### Selection criteria

- **Minimum market capitalization of $1B+, and $5B+ for mainland China.** In my view, larger Chinese companies offer more transparent financial information, and at that size international analysts routinely scrutinize their financials. The outlook for smaller mainland companies is more uncertain, and they seem to me more exposed to political and economic shifts. The mainland stocks on the list are China A-shares that can be bought through Stock Connect, for example at IBKR.
- **Taiwan and Hong Kong:** although pressure from Beijing is present, I currently treat them as safer than the mainland, which is why Hong Kong has more weight than China. The Taiwan list is built largely around TSMC, and Taiwan is governed separately from the mainland. Hong Kong's current arrangement is scheduled to run until 2047.
- **Risk is priced in.** The P/E ratios in China, Hong Kong, and Taiwan can be much lower than elsewhere, which reflects those risks.
- **Company-level factors:** expected future price, level of debt, and price-to-book (P/B) ratio.
- **Dividend tax cannot be avoided.** It can be 25–35% in some countries and 0–10% in others. Where it is higher, I required a higher expected future price to compensate.
- **Sector focus shifts over time.** The lists reflect my views at the time of selection, and they may be outdated by the time you read this. The picture changes from month to month, so caution is needed.

The most important thing I have learned is that you have to be in the right place at the right time. Decisions should be thoughtful but flexible, ready to adapt, because what worked yesterday may not work today.

### How to read the comments in watchlists.py

Every ticker line in `watchlists.py` ends with a short comment in a fixed pattern:

```python
"T": ["9984", "5802", ...],}   # Japan (Tokyo) 72 (35%)
```

- **Country (and exchange):** where the tickers on that line trade.
- **The first number (72):** how many tickers are on that line.
- **The percentage (35%):** the 1-year target price figure that applied to that country when I selected the stocks. Different countries use different values, for example because of dividend tax (see above).

The ticker count matters technically: `check_watchlists.py` compares it with the real number of tickers on the line and warns you if they differ. Keep the pattern `# Country N (xx%)` when you edit the lists (section 3.9).

## 1.6 At a glance

- Watches 1,076 tickers on 28 active markets (Asia-Pacific, Europe, the Americas; the U.S. runs as two lists) during their regular trading hours.
- Checks every market every 5 minutes while it is open (weekdays, exchange holidays skipped).
- Looks for an early reversal on 5-minute candles: price action, volume, VWAP, and RSI, with the 4-hour trend as context.
- Sends alerts to your own Telegram chat, written entirely in English:
  - 🟢 **EARLY REVERSAL LONG:** a possible buying opportunity, with Entry, Stop-loss, and Take-profit reference levels.
  - 🔴 **SELL WARNING / BEARISH REVERSAL:** a possible turn down. If you own the stock, you may want to review your position. It is not a short signal.
- Alerts are batched: those generated within the same few seconds arrive together in one message, so your phone does not buzz for every single alert.
- All times in this guide are local exchange time, except the time printed in each Telegram alert and the timestamps in the logs, which are in New York time (ET).

---

# Part 2: User guide

## 2.1 What is the screener for?

The screener watches a curated list of stocks across many exchanges and sends early reversal alerts to Telegram. It looks for the reversal on 5-minute candles (price structure, volume, VWAP, RSI) and uses the 4-hour trend for context. The 15-minute ATR is used only to calculate the stop-loss and take-profit levels (an alert is skipped if the ATR is missing).

**How to read the alerts (cash account, no short selling):**

| Alert | What it means | What it does NOT mean |
|---|---|---|
| 🟢 EARLY REVERSAL LONG | Price may be turning up. A possible buying opportunity, with the Entry / Stop-loss / Take-profit reference levels shown. | Not a guarantee. It only means a set of conditions was met. |
| 🔴 SELL WARNING / BEARISH REVERSAL | Price may be turning down. If you hold the stock, you may want to review the position. | Not a short signal. It is not about betting on a decline, so there is no stop-loss or take-profit, only the current price. |

The system does not know what is in your account, so a SELL WARNING is sent for every watched stock, not only the ones you own. You decide whether it is relevant to you. If you only want warnings about your own holdings, put just those tickers on your watchlist.

### Example alerts

The numbers below are made up and only show the layout.

```
🟢 EARLY REVERSAL LONG (🇯🇵 JAPAN)

Ticker: 1234.T
4H context: BULLISH
4H RSI / ADX: 56.3 / 24.1
5M RSI: 48.7
5M VWAP: 2812.40 JPY
5M RVOL: 2.14x
Reversal score: 9
BB width (15M): 1.85%
Entry price: 2815.00 JPY
Stop-loss: 2789.00 JPY
Take-profit: 2867.00 JPY
Status: 🟢 EARLY REVERSAL LONG
Time (New York): 20:10
```

```
🔴 SELL WARNING / BEARISH REVERSAL (🇺🇸 UNITED STATES)

Ticker: ABCD
4H context: BEARISH
4H RSI / ADX: 41.2 / 27.5
5M RSI: 52.9
5M VWAP: 63.15 USD
5M RVOL: 1.78x
Reversal score: 7
BB width (15M): 0.92%
Current price: 62.80 USD
Status: 🔴 SELL WARNING / BEARISH REVERSAL
Time (New York): 11:45
```

Section 2.4 explains every field.

## 2.2 Markets and schedule

Every country is its own market. Each one is scheduled in its own exchange's local time, so daylight saving changes are handled automatically. Scans run Monday to Friday. Exchange holidays are filtered with the `exchange_calendars` package. (If the package is not available, the scheduler still launches on holidays, but the scanner's fresh candle protection skips the stale data, so no false alerts come out of it.)

- **First scan:** 5 minutes after the session opens.
- **Last scan:** 15 minutes before the session closes.
- **Frequency:** every 5 minutes. Each market gets one scan per 5-minute slot (slots start at local minutes :00, :05, :10, and so on). Markets are scanned one after another, so a market that is later in the queue may start a minute or two after the slot begins. It is never skipped because of that.
- **Markets with a lunch break (Japan, Hong Kong, China):** the first and last scan rules apply to each session separately, and there are no scans during the break.
- **Always on:** the scheduler runs continuously, and an automatic watchdog restarts it if it ever stops (section 3.7).

| Market (run name) | Exchange(s), time zone | Session (local) | First – last scan (local) | Tickers (approx.) |
|---|---|---|---|---|
| 🇯🇵 japan | Tokyo (.T) | 09:00–11:30, 12:30–15:30 | 09:05–11:15, 12:35–15:15 | 72 |
| 🇹🇼 taiwan | Taiwan: TWSE (.TW), TPEx (.TWO) | 09:00–13:30 | 09:05–13:15 | 30 |
| 🇭🇰 hongkong | Hong Kong (.HK) | 09:30–12:00, 13:00–16:00 | 09:35–11:45, 13:05–15:45 | 155 |
| 🇰🇷 south_korea | Seoul: KOSPI (.KS), KOSDAQ (.KQ) | 09:00–15:30 | 09:05–15:15 | 82 |
| 🇨🇳 china | Shanghai (.SS) and Shenzhen (.SZ), Stock Connect names | 09:30–11:30, 13:00–15:00 | 09:35–11:15, 13:05–14:45 | 117 |
| 🇦🇺 australia | Sydney, ASX (.AX) | 10:00–16:00 | 10:05–15:45 | 25 |
| 🇩🇪 germany | Xetra (.DE) | 09:00–17:30 | 09:05–17:15 | 20 |
| 🇬🇧 united_kingdom | London (.L) | 08:00–16:30 | 08:05–16:15 | 32 |
| 🇫🇷 france | Paris (.PA) | 09:00–17:30 | 09:05–17:15 | 19 |
| 🇪🇸 spain | Madrid (.MC) | 09:00–17:30 | 09:05–17:15 | 11 |
| 🇮🇹 italy | Milan (.MI) | 09:00–17:30 | 09:05–17:15 | 6 |
| 🇧🇪 belgium | Brussels (.BR) | 09:00–17:30 | 09:05–17:15 | 2 |
| 🇳🇱 netherlands | Amsterdam (.AS) | 09:00–17:30 | 09:05–17:15 | 6 |
| 🇩🇰 denmark | Copenhagen (.CO) | 09:00–17:00 | 09:05–16:45 | 3 |
| 🇸🇪 sweden | Stockholm (.ST) | 09:00–17:30 | 09:05–17:15 | 3 |
| 🇫🇮 finland | Helsinki (.HE) | 10:00–18:30 | 10:05–18:15 | 1 |
| 🇳🇴 norway | Oslo (.OL) | 09:00–16:20 | 09:05–16:05 | 2 |
| 🇭🇺 hungary | Budapest (.BD) | 09:00–17:00 | 09:05–16:45 | 0 (not active) |
| 🇦🇹 austria | Vienna (.VI) | 09:00–17:30 | 09:05–17:15 | 1 |
| 🇨🇭 switzerland | SIX Swiss Exchange (.SW) | 09:00–17:30 | 09:05–17:15 | 3 |
| 🇹🇷 turkey | Istanbul (.IS) | 10:00–18:00 | 10:05–17:45 | 19 |
| 🇮🇱 israel | Tel Aviv (.TA) | 09:59–17:14 (Mon–Thu), Friday ends early (see note) | 10:05–16:55 | 3 |
| 🇬🇷 greece | Athens (.AT) | 10:00–17:20 | 10:05–17:05 | 3 |
| 🇵🇱 poland | Warsaw (.WA) | 09:00–17:00 | 09:05–16:45 | 2 |
| 🇨🇦 canada | Toronto: TSX (.TO), TSX Venture (.V), CSE (.CN) | 09:30–16:00 | 09:35–15:45 | 34 |
| 🇺🇸 united_states | New York (no suffix) | 09:30–16:00 | 09:35–15:45 | 310 |
| 🇺🇸 united_states2 | New York (no suffix) | 11:30–16:00 | 11:35–15:45 | 90 |
| 🇲🇽 mexico | Mexico City (.MX) | 08:30–15:00 | 08:35–14:45 | 9 |
| 🇧🇷 brazil | São Paulo, B3 (.SA) | 10:00–17:30 | 10:05–17:15 | 16 |

**Notes:**

- Ticker counts are approximate and change whenever the lists are edited. The total is currently about 1,076 tickers.
- **Inactive markets:** a market with an empty ticker list is skipped automatically. Hungary is set up and ready, and it starts on its own as soon as tickers are added.
- The exchange of each stock is identified by its Yahoo ticker suffix (.T, .KS, .HK, .DE, and so on). A ticker without a suffix is a U.S. stock.
- `united_states` and `united_states2` are two separate lists for the U.S. market, split to keep each run's download load manageable. `united_states2` holds the smaller stocks and starts later in the day, at 11:30 ET, when most European exchanges have closed. Both appear as "🇺🇸 UNITED STATES" in alerts. Only the scan schedule is shifted for `united_states2`. VWAP and 4H calculations still use the full U.S. session from 09:30.
- **Israel:** the Tel Aviv exchange trades Monday to Friday, and on Fridays it closes early (around 13:35). The scheduler uses the Monday–Thursday hours every day, so on Fridays it keeps launching scans after the close. Fresh candle protection skips the stale data, so this does not produce false alerts.
- **Mexico:** Mexico City time does not follow U.S. daylight saving. During U.S. summer time, the Mexican session ends one hour after the U.S. close, so Mexican alerts can still arrive after Wall Street has closed. In winter the two close together.
- **Order of scans:** markets that are due in the same 5-minute slot are scanned one after another, not in parallel (see section 2.7). If the queue is long, the last markets of a slot may start a little late, but they still run in that slot. A slot that has already passed is not made up afterwards.
- Local times differ from New York time depending on the season and each region's daylight saving rules. That is why this guide uses local exchange time. The time shown in the Telegram message is always New York time (ET).

How the lists were chosen is described in section 1.5.

## 2.3 How a signal is decided

### 2.3.1 4H context (the big picture)

- RSI(14) on 4H candles: above 50 → BULLISH, below 50 → BEARISH, exactly 50 → NEUTRAL.
- **Strong trend:** ADX(14) is at least 20 and the DI lines agree with the context (for BULLISH, +DI > −DI; for BEARISH, −DI > +DI).
- A signal against a strong 4H trend only passes with a score of 8 or higher (normal threshold: 6).

### 2.3.2 5M components (the last closed candle)

| Component | Meaning |
|---|---|
| VWAP | Session VWAP: restarts on the exchange's local trading day, continues after the break between sessions, and has no value outside the session. |
| RVOL | Current 5M volume divided by the median of the previous 20 candles. It is not a time-of-day RVOL, and it uses Yahoo's own volume. |
| Trap | LONG: failed breakdown (the candle dips below the lowest low of the previous 5 candles but closes back above it). SHORT: failed breakout (it pokes above the highest high but closes below it). |
| Structure | LONG: higher low (among the previous 4 candles, the two most recent have a higher low than the two before them). SHORT: lower high (the mirror image). |
| Rejection | LONG: bullish candle with a lower wick longer than 0.8× the body, closing in the upper 40% of the candle. SHORT: bearish candle with a long upper wick, closing in the lower 40%. |
| Strength | Strong close at the matching end of the candle (LONG: top 30%, SHORT: bottom 30%), with a body of at least 25% of the candle range. |
| Volume expansion | Current volume is more than 1.2 times the previous candle's volume. |
| Volume pressure | Volume expansion on a candle that closes in the signal direction (LONG: above the previous close, SHORT: below it). |
| RSI turn | The 5M RSI has turned in the signal direction versus both the previous candle and 3 candles ago. RSI is only supporting information. Overbought and oversold levels do not count. |

LONG and SHORT are the internal names of the two directions. A SHORT result is sent as a SELL WARNING / BEARISH REVERSAL, which is not a signal to open a short position.

### 2.3.3 Valid setup (prerequisite)

A score alone is not enough. A direction is a candidate only if all three conditions hold:

1. RVOL ≥ 1.30,
2. at least one price action event (trap, structure, or rejection),
3. at least one confirmation (strength, volume pressure, or RSI turn).

### 2.3.4 Score (maximum 14 points, threshold: 6)

| Item | Points |
|---|---|
| Trap (failed breakdown / breakout) | 2 |
| Structure (higher low / lower high) | 2 |
| Rejection | 1 |
| Strength | 1 |
| Volume expansion | 1 |
| Volume pressure | 1 |
| RSI turn | 1 |
| RVOL ≥ 1.30 | 1 |
| RVOL ≥ 1.70 (in addition to the above) | +1 |
| VWAP: LONG price at or above VWAP (reclaim), SHORT at or below it (rejection) | 2 |
| Near VWAP on the "wrong" side (within 0.3%) | 1 (instead of the 2 points) |
| 4H context matches the direction | 1 |

### 2.3.5 Direction and filters

- If both LONG and SHORT are valid and reach the threshold, the higher score wins (on a tie, LONG).
- **Trend filter:** a signal against a strong 4H trend passes only with 8+ points.
- **Duplicate protection:** the same candle and direction never triggers two alerts.
- **Cooldown:** at most one alert per stock in the same direction every 60 minutes. An alert in the opposite direction goes through even during the cooldown.
- If the 15M ATR or Bollinger value is missing, the alert is skipped.

### 2.3.6 Exit levels (LONG only)

- **Entry:** the closing price of the last closed 5M candle.
- **Stop-loss:** Entry − 4 × ATR(14, 15M).
- **Take-profit:** Entry + 8 × ATR(14, 15M).

This gives a 1:2 risk/reward ratio. These levels are reference values calculated by fixed rules, not recommendations. The system does not trade.

## 2.4 Alert fields and delivery

### Fields

| Field | Meaning |
|---|---|
| Title | Alert type, with the market's flag and name, e.g. "🟢 EARLY REVERSAL LONG (🇯🇵 JAPAN)". |
| Ticker | The Yahoo symbol, including its exchange suffix (U.S. stocks have none). |
| 4H context | BULLISH / BEARISH / NEUTRAL. |
| 4H RSI / ADX | The 4H RSI and ADX values. |
| 5M RSI | The 5-minute RSI. |
| 5M VWAP | Session VWAP, with the currency code. |
| 5M RVOL | Relative volume (see 2.3.2). |
| Reversal score | The score (6–14). |
| BB width (15M) | Bollinger band width in %, a measure of volatility (information only). |
| Entry price / Stop-loss / Take-profit | LONG alerts only. |
| Current price | SELL WARNING only. |
| Status | The alert type again, as a one-line summary. |
| Time (New York) | When the alert was generated, in New York time (ET). |

Prices are shown with the currency code of the stock's exchange: JPY, TWD, HKD, KRW, CNY, AUD, EUR, GBX, DKK, SEK, NOK, HUF, CHF, TRY, ILS, PLN, CAD, USD, MXN, BRL.

London (.L) prices are quoted by Yahoo in pence (1/100 of a pound). London alerts are therefore labeled GBX (pence), not GBP. Divide the number by 100 to get pounds.

### Delivery: batched messages

Alerts are not sent one by one. This is what keeps the number of notifications low:

- Each alert goes into a queue. A background sender empties the queue every 5 seconds.
- Alerts that are waiting at the same time are combined into one message, separated by a line (`──────────`). A message holds up to about 3,900 characters, safely below Telegram's limit of 4,096. If more alerts are waiting, they continue in the next message.
- The sender keeps to roughly one message per second per chat.
- If Telegram asks the sender to slow down (HTTP 429), it waits the requested time and tries again. If Telegram rejects the Markdown formatting, the message is sent again as plain text. Each message gets up to 3 attempts.
- If a message still cannot be sent, the alerts are saved to an outbox (`state/telegram_outbox.json`) and retried automatically at the start of the next scanner run. A delayed alert still shows the time it was generated.
- Alerts are sent only to the single chat ID set in `RSI_search.py` (`TELEGRAM_CHAT_ID`).

## 2.5 Data and reliability

**Source:** Yahoo Finance (yfinance). For some exchanges Yahoo delivers data with a delay of 15–30 minutes or more.

**Three timeframes:**

| Timeframe | Purpose | Cold start | Refreshed when cache age exceeds | Cache size |
|---|---|---|---|---|
| 5-minute | Finding the signal | 5 days | 4 minutes | 200 candles |
| 15-minute | ATR (stop-loss / take-profit) and Bollinger width | 5 days | 14 minutes | 200 candles |
| 1-hour → 4-hour | Trend context | 2 months (China: 6 months) | 59 minutes | 400 candles |

*Cold start* is the amount of history downloaded the first time a market or ticker is loaded (or after the cache has been cleared).

**Cache and catch-up:** the cache refreshes by age. If the cache is fresh, nothing is downloaded. Missed candles are filled in based on the age of the cache's last candle:

- up to 6 hours: reloads only today,
- up to 6 days: reloads the last 5 trading days (catch-up after a weekend, holiday, or downtime, which also overwrites earlier partial candles),
- older than that: full cold start.

**Download:** in batches of 250 stocks, with a 5-second pause between batches (Yahoo protection).

**4H candles:** Yahoo does not provide 4-hour candles, so they are built from hourly data. Blocks are based on trading minutes counted from the open (240 minutes per block), and a lunch break does not count. If the trading day is not a multiple of 240 minutes, the end of the day forms a shorter final block (for example, a Tokyo day is 240 + 90 minutes). The last, not-yet-closed block is dropped. China's 4-hour trading day is exactly one block.

**Data protections:**

- **Closed candles only:** the last, not-yet-closed candle is always dropped (prevents look-ahead bias).
- **Session filter:** only candles inside the official session remain in the 5-minute data.
- **Fresh candle protection:** if the last closed 5M candle is older than 60 minutes, the stock is skipped (exchange closed, holiday, lunch break, or no fresh Yahoo data). This prevents stale alerts.
- **Warm-up:** at least 60 candles are required on all three timeframes (5M, 15M, 4H), otherwise the stock is skipped.
- **Data gap check:** if a timestamp is missing within the same day and session, a warning is printed (informational only, the run is not stopped).
- **1H cache integrity:** a corrupted or invalid 1H cache is discarded and reloaded.
- **One run per market at a time:** a lock prevents the same market from running twice at once. A stale lock left by a crashed run is released automatically.
- **Time-boxed runs:** a scanner run that takes longer than 295 seconds is stopped, so it can never overlap the next 5-minute slot.

## 2.6 Frequently asked questions

**Why did I get a SELL WARNING for a stock I don't own?**
The screener does not know your portfolio, so it warns about every watched stock. Ignore the ones you don't hold, or trim your watchlist to your own holdings (section 3.9).

**Why is there no alert for a stock I'm watching?**
The conditions in section 2.3 are deliberately strict. A stock is also skipped when its market is closed, its data is stale or still warming up, a duplicate or cooldown applies, or it is not on the watchlist.

**The price already moved when I read the alert. Why?**
The alert describes the last closed 5-minute candle. Scans run on 5-minute slots, Yahoo data can be 15–30 minutes or more late on some exchanges, and a message needs a moment to arrive. Treat the Entry price as a reference, not a live quote.

**Why are there no scans in the first 5 and last 15 minutes of a session?**
By design: the first scan waits 5 minutes after the open, and the last scan runs 15 minutes before the close.

**Why does a London price look 100 times too big?**
London prices are in pence. Divide by 100 for pounds (section 2.4).

**Why did several alerts arrive in one message?**
Alerts are batched every 5 seconds to keep the number of notifications low (section 2.4).

**Does a higher score mean a better trade?**
A higher score means more conditions were met. It has not been tested as a predictor of profit (see section 2.7).

**Can I add ETFs or other symbols?**
Technically, any symbol that Yahoo provides intraday data for, and whose exchange suffix is known to `markets.py`, can be added. The selection criteria in this guide were designed for stocks, and the shipped lists follow them.

**Can I get the alerts in a group or channel?**
The current version sends alerts to one personal chat. Group, channel, and topic delivery has been removed.

**Who can help me with installation questions?**
See section 4.1.

## 2.7 Limitations and important notes

- **Not financial advice.** The alerts are the output of a mechanical rule set. Decisions and risk are entirely yours.
- **No backtesting.** The thresholds (score, RVOL, ATR multipliers) are settings, not proven optimized values. The engine is tuned for the earliest possible signal, so it accepts a fair amount of noise.
- **Yahoo data:** may be delayed (15–30 minutes or more on some exchanges), and volume may differ from your broker's (e.g. IBKR) or TradingView's. RVOL is therefore only meaningful relative to Yahoo's own data.
- **Yahoo data terms.** Yahoo's free data is generally meant for personal, non-commercial use. The software license gives you no rights to Yahoo data, so check Yahoo's terms before using the screener for anything other than your own personal monitoring (section 4.4).
- **Illiquid stocks:** if many candles have low or zero volume, RVOL (based on the median) can spike. Alerts may be noisier, especially in smaller markets (e.g. Mexico).
- **Trading costs and currency risk:** the alert does not account for commissions, spreads, or exchange rates.
- **Holidays and early closes:** holidays are filtered by the calendar, but early closes are not known to the scheduler. On such days the last scan happens at the time based on the normal close, and fresh candle protection filters out stale data.
- **Scans are sequential.** Markets due in the same 5-minute slot run one after another. A market that is later in the queue may start a minute or two after the slot begins, but it still runs in that slot. Quiet markets are quick, and the largest lists take the longest. A slot is only missed if the whole queue takes longer than 5 minutes (rare). In that case the scheduler continues with the current slot and does not make up the missed one.
- **Last 15 minutes of every session:** no scans run there, so a reversal that forms late in the session is not reported.
- **Availability:** the screener is only as available as your server, your internet connection, Yahoo, and Telegram (section 4.3).

## 2.8 Glossary

| Term | Meaning |
|---|---|
| RSI | Relative Strength Index, a 0–100 momentum indicator. Here it is used for direction (above/below 50 on 4H) and for the "turn" of momentum on 5M. |
| ATR | Average True Range, the typical size of a candle's movement. Used to set stop-loss and take-profit distances. |
| ADX / DI | Trend strength (ADX) and direction (+DI / −DI). ADX of 20 or more counts as a strong trend here. |
| VWAP | Volume-Weighted Average Price for the session. Price above VWAP means buyers are in control on average. |
| RVOL | Relative volume: how current volume compares with the recent median. 2.0x means twice the usual volume. |
| Bollinger band width | The width of the Bollinger bands as a percentage of price. A wider band means more volatility. |
| 4H candle | A candle covering four hours of trading time, built from hourly data. |
| GBX | British pence, 1/100 of a pound. |
| Cold start | The first, larger data download for a market, or after the cache was cleared. |
| Watchdog | The cron entry that restarts the scheduler within a minute if it has stopped. |
| Bot token | The secret key that lets the program send messages as your Telegram bot. |
| Chat ID | The number that tells Telegram which chat should receive the alerts. |
| Venv | A Python virtual environment: a private folder with the Python packages the screener needs. |

---

# Part 3: Operator guide (installing and running it)

This part is for whoever runs the screener on a server, which now means every user. It takes you from an empty server to a screener that runs around the clock and restarts itself. You do not need to be a programmer, but you do need to be comfortable typing commands in a terminal.

## 3.1 Architecture and files

```
cron (every minute)
  └─ flock (guarantees only ONE scheduler)
       └─ scheduler.py            runs continuously, checks every 10 seconds
            └─ RSI_search.py <market>     one run per due market, then exits
                 ├─ Yahoo Finance (5M, 15M, 1H data) → cache/
                 ├─ analysis per ticker → state/ (duplicates, cooldown)
                 └─ Telegram queue → your chat
```

| File / folder | Role |
|---|---|
| `markets.py` | The single place for markets. Exchanges (time zone, sessions, suffixes, flag, currency) and runnable markets (`RUNS`). Both the scheduler and the scanner read it. It also holds the shared log writer. |
| `scheduler.py` | Runs continuously (started from cron with flock, restarted by the cron watchdog). Every 10 seconds it checks which markets are due and launches the scanner for each, one after another. |
| `RSI_search.py` | The scanner: evaluates one market, then exits. Its argument is the run name (e.g. `japan`). It also holds your `TELEGRAM_CHAT_ID` setting. |
| `watchlists.py` | The watched tickers: `<market>_watchlist_by_suffix` dictionaries. |
| `check_watchlists.py` | The checker for `watchlists.py` (sections 3.6 and 3.10). |
| `secrets.env` | Your `TELEGRAM_TOKEN`. Not part of the download. An environment variable of the same name takes priority over the file. |
| `cache/` | Downloaded Yahoo data (`<market>_5m.pkl`, `_15m.pkl`, `_1h.pkl`). Safe to delete. |
| `state/` | `state_<market>.json` (last alert per symbol, for duplicate and cooldown protection) and the Telegram outbox. |
| `lock/` | Per-market lock file. |
| `log/` | Daily run log, error log, Telegram statistics. |
| `venv/` | The Python environment. It must be named `venv` and sit next to the scripts, because the scheduler starts the scanner with `venv/bin/python`. |

**Scheduler details:**

- Checks every 10 seconds (`CHECK_INTERVAL`).
- Reloads `watchlists.py` about once a minute. A syntax error keeps the previous version in use and prints a warning.
- Skips markets whose ticker list is empty or missing.
- Stops a scanner run after 295 seconds (`SCANNER_TIMEOUT`). Runs slower than 120 seconds (`SLOW_RUN_SEC`) are noted in the daily log.
- Runs the scanner for one market at a time. The scanner opens its own short-lived process every time, so a crash in one run never takes the scheduler down.

## 3.2 What you need

### Server

The screener is a long-running background program. It needs a place where a process can run all day, every weekday.

| Option | Suitable? | Notes |
|---|---|---|
| VPS or dedicated server (Linux) | Best choice | Full control, a stable IP address, no process limits. This is what I recommend. |
| cPanel hosting on a VPS or dedicated server | Good | You get the Cron Jobs tool and a terminal. This works well. |
| Shared hosting with cPanel | Only if the host allows it | Many shared hosts limit or kill long-running processes, and shared IP addresses can get throttled by Yahoo because of other customers. Ask your host first whether a permanently running Python process, cron every minute, and SSH access are allowed. |
| Home computer or Raspberry Pi (Linux) | Works | Must run 24/7 on a stable connection. |
| Windows | Not supported out of the box | The scheduler calls `venv/bin/python` and the watchdog uses `flock`, which are Linux tools. If you use Windows, run the screener on a Linux server (a small VPS is enough) or inside WSL. |
| macOS | Not supported out of the box | `flock` is not installed by default, and a laptop that sleeps will miss scans. Use a Linux server. |

You do not need a web server, a database, a GPU, or any open inbound port. The screener only makes outbound HTTPS connections.

### Resources

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 1 GB | 2 GB |
| Free disk space | 2 GB | 5 GB |
| Network | Stable outbound HTTPS | Stable outbound HTTPS and a dedicated (not shared) IP address |

These are conservative estimates based on how the program works (the cache files add up to tens of megabytes, and the memory peak is a few hundred megabytes), not formal benchmarks. The scheduler runs only one scanner at a time, so extra CPU cores do not make it parallel, but a faster CPU and connection shorten each run. Remember that every run must finish within 295 seconds. If your server is slow, start with a smaller watchlist and watch the `SLOW run` lines in the log (section 3.12).

### Software

- Linux with cron and `flock` (part of the standard util-linux package).
- Python 3.10 or newer (3.11 or 3.12 is recommended). Check with `python3 --version`.
- These Python packages, installed into the venv (section 3.3): `yfinance`, `pandas`, `numpy`, `requests`, `exchange_calendars`, and `tzdata`.
  - `exchange_calendars` is optional but strongly recommended, because it filters exchange holidays.
  - `tzdata` makes sure Python has the time zone database even if the server has none.
- An accurate server clock. The screener compares candle times with the current time to decide whether data is fresh. Keep the clock synchronized (NTP, which is the default on most servers). The server's own time zone does not matter.

### Accounts

- A Telegram account, and a bot that you create for free (section 3.4).
- No account with Yahoo, with me, or with any data vendor.

## 3.3 Installation step by step

The commands below assume a Linux server with SSH or a cPanel terminal. Replace `USER` with your own account name. Install the screener outside any web folder: in cPanel, use `/home/USER/rsi-scanner`, never `public_html`. That way the web server can never serve your files.

**Step 1: Create the folder and upload the files.**

```bash
mkdir -p ~/rsi-scanner
cd ~/rsi-scanner
```

Upload `RSI_search.py`, `scheduler.py`, `markets.py`, `watchlists.py`, and `check_watchlists.py` into this folder (SFTP, the cPanel File Manager, or scp). Unpack the download first if it came as a zip.

**Step 2: Check your Python version.**

```bash
python3 --version
```

You need 3.10 or newer. If it is older, ask your host for a newer Python, or look for `python3.11` or `python3.12`, and use that name in the next step.

**Step 3: Create the virtual environment (it must be called `venv`).**

```bash
python3 -m venv venv
```

**Step 4: Install the packages.**

```bash
venv/bin/pip install --upgrade pip
venv/bin/pip install yfinance pandas numpy requests exchange_calendars tzdata
```

**Step 5: Create the working folders.**

```bash
mkdir -p cache state lock log
```

The program creates these automatically, but create them now so that the cron line in section 3.7 can write its output file from the very first minute.

**Step 6: Set up Telegram, `secrets.env`, and your chat ID.** Follow sections 3.4 and 3.5.

**Step 7: Run the checks and the first test.** Follow section 3.6.

**Step 8: Start the around-the-clock operation.** Follow section 3.7.

## 3.4 Telegram setup

Alerts are sent by your own bot to your own personal chat. This takes about five minutes.

1. **Create the bot.** In Telegram, open the chat with `@BotFather` and send `/newbot`. Choose a name and a username (the username must end in `bot`). BotFather replies with the bot token, a long string like `123456789:AA...`. The token works like a password.
2. **Start your bot.** Search for your new bot by its username, open it, and press Start (or send any message). This step is required, because a bot can never send the first message to a person.
3. **Find your chat ID.** After you have messaged the bot, open this address in a browser, with your own token in place of `<TOKEN>`:

   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

   Use a private or incognito window, because your browser would otherwise save the token in its history, and clear the history afterwards. In the reply, look for `"chat":{"id":123456789`. That number is your personal chat ID (for a private chat it is a positive number). If the reply is empty, send your bot another message and reload the page. Enter this number in `RSI_search.py` as `TELEGRAM_CHAT_ID` (the line shown in section 1.2).

4. **Optional test message** (from your server's terminal):

   ```bash
   curl -s "https://api.telegram.org/bot<TOKEN>/sendMessage" -d chat_id=<CHAT_ID> -d text="FinHavenArc test"
   ```

   If the message arrives, the token and the chat ID are correct.

5. **Optional: admin notifications.** If you also want a private message when something critical goes wrong (a crash or a failed download), open `RSI_search.py` and set `TELEGRAM_ADMIN_CHAT_ID` near the top to the same chat ID, for example `TELEGRAM_ADMIN_CHAT_ID = "123456789"`. The default is `None` (off). The same error sends at most one message every 30 minutes.

If you ever think your token has leaked, send `/revoke` to `@BotFather`, get a new token, and update `secrets.env`.

## 3.5 The secrets.env file

Create a file named `secrets.env` in the same folder as the scripts, with exactly this one line:

```
TELEGRAM_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Rules for this file:

- No spaces around `=`. Write `KEY=value`, not `KEY = value`.
- No quotation marks around the values, and no `export` in front of the names.
- One setting per line. Lines that start with `#` are ignored.
- Protect the file so that only you can read it:

  ```bash
  chmod 600 secrets.env
  ```

Instead of the file, you can set an environment variable with the same name. It takes priority over the file. If the token is missing, the scanner stops at startup with the message `Missing secret: TELEGRAM_TOKEN`. Your chat ID is not stored here. It is set in `RSI_search.py` (section 3.4).

## 3.6 Pre-flight check, first test run, and pre-warming

**1. Check the watchlists.**

```bash
venv/bin/python check_watchlists.py
```

This verifies the syntax of `watchlists.py`, that every market has a list, that suffixes match the exchanges, that there are no duplicate or invalid tickers, and that the ticker counts in the comments are correct. ❌ lines are errors that must be fixed, and ⚠️ lines are warnings. With the shipped lists, the clean result is `Done: 0 errors, 1 warnings.`, where the one warning is Hungary's intentionally empty list.

Optionally, also test whether Yahoo accepts every ticker (about 1–2 minutes, best on a weekday):

```bash
venv/bin/python check_watchlists.py --yahoo
```

Section 3.10 explains the checker in detail.

**2. Run one market by hand.**

```bash
venv/bin/python RSI_search.py japan
```

You should see a line like `[2026-10-05 20:30:00] Current market: 🇯🇵 JAPAN. 72 stocks to check...` and, after the download and analysis, a line like `Summary (japan): no_signal=60, stale_candle=11`. If the market is closed, every stock shows `stale_candle`, which is normal. A manual run is not subject to the scheduler's 295-second time limit.

**3. Pre-warm the other markets (recommended).** The first run of every market downloads the full history (cold start), which takes longer than a normal run. Doing this by hand once avoids timeouts in the first scheduled runs. Run the markets one at a time, with a short pause between them, so you do not strain Yahoo:

```bash
venv/bin/python RSI_search.py china
venv/bin/python RSI_search.py hongkong
# ...and so on for each market you want to use
```

If a scheduled cold start is stopped by the 295-second limit, the data that was already saved is kept, and the next run continues from there.

## 3.7 Running it around the clock

The screener has to run constantly, and it has to come back by itself after a crash, a restart of the program, or a reboot of the server. The method uses cron with `flock`:

- cron starts the same command every minute.
- `flock -n` refuses to start a second copy while one is already running, so there is always exactly one scheduler.
- If the scheduler ever stops, the next cron minute starts it again. After a server reboot, cron starts it too. This is the watchdog.

The cron line (one single line, with your own paths):

```
* * * * * /usr/bin/flock -n /home/USER/rsi-scanner/scheduler.flock /home/USER/rsi-scanner/venv/bin/python /home/USER/rsi-scanner/scheduler.py >> /home/USER/rsi-scanner/log/scheduler.out 2>&1
```

- Use absolute paths everywhere. Cron has almost no environment.
- Check the location of `flock` with `which flock` and adjust `/usr/bin/flock` if needed.
- The `scheduler.flock` file is created by flock itself. It is a different file from the per-market lock files in `lock/`.
- `>> log/scheduler.out 2>&1` keeps the console output (data gap warnings, Telegram error codes) and stops cron from emailing you every minute.

**Adding it in cPanel:**

1. Log in to cPanel and open Advanced → Cron Jobs.
2. Optionally set a Cron Email address, or leave it empty. The redirect in the line above already silences normal output.
3. Under Add New Cron Job, choose Once Per Minute (`* * * * *`) in Common Settings.
4. Paste the command part of the line above (everything after `* * * * *`) into the Command field.
5. Click Add New Cron Job.

**Adding it over SSH instead:** run `crontab -e`, paste the full line, save, and exit.

**Check that it works** (wait one or two minutes):

```bash
ps aux | grep scheduler.py | grep -v grep
tail -n 20 ~/rsi-scanner/log/scheduler.out
```

You should see one `scheduler.py` process, and the output file should show the banner `FinHavenArc Screener Scheduler started` with the list of active markets. During market hours, the daily log (section 3.12) gets a new line for every run.

**Alternative for a VPS where you have root: systemd.** If you prefer a system service to cron, this does the same job. Use one method or the other, never both.

```ini
[Unit]
Description=FinHavenArc Screener scheduler
After=network-online.target

[Service]
User=USER
WorkingDirectory=/home/USER/rsi-scanner
ExecStart=/home/USER/rsi-scanner/venv/bin/python scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 3.8 Stopping, restarting, and updating

**What needs a restart?**

| Change | Restart? |
|---|---|
| `RSI_search.py`, `watchlists.py` | No. The next run already uses the new version (the scheduler also reloads `watchlists.py` about once a minute). |
| `scheduler.py`, `markets.py` | Yes. Stop the scheduler (below). The cron watchdog starts it again within a minute. |
| `secrets.env` | No for the scanner (it is read at the start of every run). |
| Python packages (`pip install -U ...`) | The next scanner run uses them. Restart the scheduler as well to be safe. |

**Restart the scheduler:**

```bash
pkill -f scheduler.py
```

Within about a minute, cron starts a fresh copy. A scanner run that is in progress finishes on its own.

**Stop it permanently:** first remove (or comment out) the cron line, then run `pkill -f scheduler.py`. If you stop it first, cron simply starts it again.

**Updating to a newer package:**

1. Back up your own `RSI_search.py` (it holds your chat ID and any settings you changed), `watchlists.py`, `markets.py` (if you edited it), and `secrets.env`.
2. Copy the new `RSI_search.py`, `scheduler.py`, and `check_watchlists.py` over the old ones. Then enter your `TELEGRAM_CHAT_ID` (and any other setting you changed, such as `TELEGRAM_ADMIN_CHAT_ID`) in the new `RSI_search.py` again.
3. Do not blindly overwrite `watchlists.py` or `markets.py`. Compare the new files with yours and carry over your own changes. A new `watchlists.py`, if one is published, reflects my latest review of the shipped lists.
4. Run `venv/bin/python check_watchlists.py`, then restart the scheduler if `scheduler.py` or `markets.py` changed.

## 3.9 Configuration reference

### Editing watchlists.py

```python
japan_watchlist_by_suffix = {
    "T": ["9984", "5802", "6723"],}   # Japan (Tokyo) 3 (35%)
```

- Every market has one dictionary named `<watchlist>_watchlist_by_suffix`. The keys are Yahoo suffixes (`"T"`, `"HK"`, `"KS"`, `"DE"`, …). U.S. tickers use the key `"USA"` and get no suffix.
- Write tickers in quotes, without the suffix, exactly as Yahoo writes the base symbol: `"0700"` (leading zeros matter), `"000660"`, `"ALK-B"`. The program adds the suffix itself.
- **Closing brace:** put the final `}` before the `#` comment. A `}` behind a comment is part of the comment and causes a syntax error.
- **Comment pattern:** keep `# Country N (xx%)` at the end of each ticker line. N must equal the number of tickers on the line, because `check_watchlists.py` compares them. The percentage is the 1-year target price figure (section 1.5).
- **Switch a market off** by emptying its list (`[]`). Fill an empty list to switch it on again.
- **Your own holdings only?** Replace a list with just your tickers. SELL WARNINGs then concern only what you own.
- **Capacity:** keep each market's list at or below 500 tickers (2 × 250), and keep the total of each region (Asia-Pacific, Europe, the Americas) within the same cap, because markets whose trading hours overlap share the same download budget. Markets run one after another, so large overlapping lists lengthen every run.

After every change, run `venv/bin/python check_watchlists.py`.

### Adding a market or exchange (markets.py)

- **New exchange:** add one line to the `_EXCHANGES` list (key, flag, currency, time zone, suffixes, sessions).
- **New runnable market:** add one line to `RUNS` (label, exchange, calendar code, watchlist name; optional `start` to shift the scan schedule).
- **Watchlist:** `<watchlist>_watchlist_by_suffix` in `watchlists.py`.

Keep underscores out of the labels in `RUNS`, because Telegram's Markdown formatting would misread them. Exchanges sometimes change their trading hours. If that happens, edit the sessions of that exchange in `markets.py` and restart the scheduler.

### Main parameters

| Parameter | Default | Where | Effect |
|---|---|---|---|
| `REVERSAL_SCORE_MIN` | 6 | RSI_search.py | Minimum score for an alert. |
| `REVERSAL_SCORE_STRONG_AGAINST_TREND` | 8 | RSI_search.py | Threshold for a signal against a strong 4H trend. |
| `REVERSAL_RVOL_MIN` / `_STRONG` | 1.30 / 1.70 | RSI_search.py | RVOL thresholds. |
| `ALERT_COOLDOWN_MIN` | 60 | RSI_search.py | Pause between same-direction alerts (minutes). |
| `SL_ATR_MULT` / `TP_ATR_MULT` | 4.0 / 8.0 | RSI_search.py | Stop-loss and take-profit multipliers. |
| `ADX_4H_MIN` | 20 | RSI_search.py | ADX level at which the 4H trend counts as strong. |
| `MAX_SIGNAL_BAR_AGE_MIN` | 60 | RSI_search.py | Older candles are not evaluated. |
| `WARMUP_BARS` | 60 | RSI_search.py | Minimum candles per timeframe. |
| `BATCH_SIZE` / `BATCH_PAUSE_SEC` | 250 / 5 | RSI_search.py | Yahoo download batch size and pause between batches (seconds). Lowering the pause or raising the batch size raises the risk of being throttled. |
| `TELEGRAM_BATCH_INTERVAL_SEC` | 5 | RSI_search.py | How often the alert queue is sent. |
| `TELEGRAM_MAX_LEN` | 3900 | RSI_search.py | Maximum characters per Telegram message (Telegram's limit is 4096). |
| `TELEGRAM_CHAT_ID` | your chat ID | RSI_search.py | The personal chat that receives the alerts (section 3.4). |
| `TELEGRAM_ADMIN_CHAT_ID` | None | RSI_search.py | Optional private chat for critical error messages. |
| `OPEN_DELAY` / `CLOSE_DELAY` | 5 / 15 | markets.py | Minutes after the open for the first scan, and before the close for the last scan. |
| `CHECK_INTERVAL` | 10 | scheduler.py | Seconds between the scheduler's checks. |
| `SCANNER_TIMEOUT` | 295 | scheduler.py | Seconds after which a scanner run is stopped. |
| `SLOW_RUN_SEC` | 120 | scheduler.py | Runs slower than this are noted in the daily log. |

Remember that the thresholds are settings, not proven optimized values (section 2.7).

## 3.10 The watchlist checker (check_watchlists.py)

### What it is for

`watchlists.py` is the file you will edit most often, and it is plain Python. One missing quotation mark, a stray bracket, a number without quotes, or a wrong exchange suffix can switch a whole market off, or silently leave tickers without data, and you would only notice when no alerts arrive. `check_watchlists.py` is a safety net for exactly that. It tests two things:

1. **The standard check** (always, in a second): is `watchlists.py` correct and consistent with `markets.py`?
2. **The Yahoo check** (optional, with `--yahoo`, about 1–2 minutes): does Yahoo actually deliver data for every ticker, in the exact form in which the scanner requests it?

The checker is read-only. It sends no Telegram messages, and it does not change your lists, the cache, or the alert state. You can run it at any time, even while the scheduler is running. The `--yahoo` option does make requests to Yahoo from your server's IP address, so avoid running it at the same moment as other heavy activity (for example the top of the hour, when all markets refresh their hourly data).

### How to run it

```bash
cd ~/rsi-scanner
venv/bin/python check_watchlists.py            # standard check
venv/bin/python check_watchlists.py --yahoo    # standard check plus the Yahoo test
```

Run it: after every edit of `watchlists.py` (and of the market definitions in `markets.py`), before you start the screener for the first time, once a month with `--yahoo` on a weekday, and after you update yfinance.

### What the standard check verifies

Lines that start with ❌ are errors that you must fix. Lines that start with ⚠️ are warnings.

| # | Check | Result | Example message |
|---|---|---|---|
| 1 | Syntax of `watchlists.py`. If the file cannot be read, the checker stops here, shows the line number and the text of the offending line, and gives a tip. | ❌ | `❌ watchlists.py SYNTAX ERROR: ... (line 12)` and `Tip: don't put the closing } after a # comment.` |
| 2 | Every runnable market has a list. For every market in `RUNS`, the dictionary `<watchlist>_watchlist_by_suffix` must exist. | ❌ | `❌ japan: watchlists.japan_watchlist_by_suffix is missing` |
| 3 | Empty lists are reported. The scheduler skips such a market, which is correct if it is intended. | ⚠️ | `⚠️ hungary: empty watchlist (the scheduler will skip it)` |
| 4 | Suffix matches the exchange. For example, a `"HK"` key in the Japan list is an error. The `"USA"` key is always allowed. | ❌ | `❌ japan: the 'HK' suffix does not belong to the japan exchange` |
| 5 | Duplicate tickers inside the same suffix list. | ❌ | `❌ japan/T: duplicate ticker: ['7203']` |
| 6 | Invalid tickers: not text (for example `9984` written without quotes), empty, or containing a space. | ❌ | `❌ japan/T: invalid ticker: [9984]` |
| 7 | Orphan lists. A dictionary named `..._watchlist_by_suffix` that no market uses, usually because of a typo in its name. | ⚠️ | `⚠️ jpan_watchlist_by_suffix: no matching market in RUNS (typo?)` |
| 8 | Comment count. The number in the line's trailing comment (`# Japan (Tokyo) 72 (35%)`) must equal the real number of tickers on the line. | ⚠️ | `⚠️ line 12 (T): the comment says 72 tickers, but the list contains 71` |

At the end it prints a summary:

```
Done: 0 errors, 1 warnings.
```

Hungary is expected to produce one warning, because its list is intentionally empty, so `Done: 0 errors, 1 warnings.` is a normal, clean result with the shipped lists. The exit code of the program is 1 if there was at least one error and 0 otherwise, so you can also use it in scripts.

**What it does not check:** it does not check duplicates between different markets, it does not check the 500-ticker limit of section 3.9, and it does not check whether a ticker really exists. Only the Yahoo test can do that last one. The comment-count check only looks at lines where the suffix and the whole list are on the same line, in the pattern shown in section 3.9. Lists spread over several lines are not covered by that particular check.

### What the Yahoo check does (--yahoo)

- It collects every ticker of every market as the scanner will request it (the base symbol plus its suffix, for example `0700.HK`).
- It downloads 5 days of 5-minute data, the same data type and interval that the scanner uses, in batches of 250 tickers with a 5-second pause between batches (the same Yahoo-protection rules as the scanner).
- A ticker is OK only if Yahoo returned at least one real closing price for it. Otherwise it is listed as failed, together with the (shortened) reason that Yahoo gave, or `no data`.
- For failed tickers that carry a suffix with a known alternative, it tries the alternative automatically with daily data and prints a hint when the alternative works:
  - Taiwan: `.TW` ↔ `.TWO`
  - South Korea: `.KS` ↔ `.KQ`
  - Canada: `.TO` → `.V` or `.CN`
- It prints the failures grouped by market, then a final summary.

**Example of a clean result:**

```
Yahoo check: 1076 tickers (5-minute data, same as the scanner uses)...
✅ Yahoo accepted all 1076 tickers.

Done: 0 errors, 1 warnings.
```

**Example with problems:**

```
Yahoo check: 1076 tickers (5-minute data, same as the scanner uses)...
⚠️  taiwan: 2 tickers could not be retrieved from Yahoo
      8210.TW      no data  -> maybe: 8210.TWO
      6584.TWO     no data
⚠️  hongkong: 1 tickers could not be retrieved from Yahoo
      0001.HK      no data

Total: 3/1076 tickers failed. (On weekends, intraday data may be missing for some markets; for a final verdict, it's worth running this on a weekday as well.)

Done: 0 errors, 4 warnings.
```

Yahoo failures are warnings, not errors, because they can be temporary.

### How to read and fix the results

| What you see | What it usually means | What to do |
|---|---|---|
| A ticker with `-> maybe: <other suffix>` | The ticker is on the other exchange of the same country. | Move it to the other suffix list in `watchlists.py`, and update the comment counts. |
| A single ticker with `no data`, others in that market are fine | The company was delisted or renamed, the code changed, trading is suspended, or the stock is very illiquid. | Look the ticker up on finance.yahoo.com. Correct the code, or remove it. |
| Almost all tickers of one market fail | That market is closed for a holiday or the weekend (intraday data missing), or Yahoo is throttling you. | Run it again on a normal weekday, after a pause. |
| Failures all over many markets | Yahoo is throttling your IP, or yfinance is outdated. | Wait and retry. Update yfinance (section 3.11). Make sure no second copy runs from the same IP. |

After fixing, run the standard check again, and run `--yahoo` again until you are satisfied.

**Technical note:** the Yahoo test reads error details from an internal part of the yfinance library. If a future yfinance version changes that, the `--yahoo` option may stop working, while the standard check keeps working. In that case, please tell me (section 4.1). The scanner itself is not affected.

## 3.11 Routine maintenance

**Monthly**

- Review your watchlists. Remove stocks you no longer want, and compare with the newest shipped `watchlists.py`, if a newer one has been published.
- Run `venv/bin/python check_watchlists.py --yahoo` on a weekday to find tickers that Yahoo no longer accepts, and fix them.
- Update the data library, because Yahoo changes things from time to time and yfinance follows:

  ```bash
  venv/bin/pip install --upgrade yfinance
  ```

  If many tickers suddenly show `no_data` for all markets, an outdated yfinance is the most common cause.
- Glance at the error logs (section 3.12) and at the free disk space.

**Yearly**

- Update the holiday calendars: `venv/bin/pip install --upgrade exchange_calendars`.
- Check that the exchange hours in `markets.py` still match the exchanges' official hours.

**Housekeeping**

- The daily logs are small, but they accumulate. This deletes logs older than 60 days:

  ```bash
  find ~/rsi-scanner/log -name '*.log' -mtime +60 -delete
  find ~/rsi-scanner/log -name '*.json' -mtime +60 -delete
  ```

- `log/scheduler.out` grows without limit. Empty it now and then with `: > ~/rsi-scanner/log/scheduler.out`.
- **Clearing the cache:** if the data looks suspicious (for example many `warmup`), delete `cache/<market>_*.pkl` and the next run reloads it. The `state/` folder is not affected.

**Backups**

Back up `RSI_search.py` (your chat ID and settings), `watchlists.py`, `markets.py` (if you edited it), and `secrets.env` (store this one securely). The `cache/` folder can always be rebuilt, and `state/` only holds alert history.

**Testing the full evaluation on a closed market**

For a closed market every stock shows `stale_candle`. To test the whole evaluation anyway, you can temporarily raise `MAX_SIGNAL_BAR_AGE_MIN`. You must set it back to 60 afterward, and delete that market's state file (`state/state_<market>.json`) after any alerts were sent.

## 3.12 Logging and monitoring

**Daily run log:** `log/YYYY_MM_DD.log` (by New York date, with timestamps in New York time). One line per run:

```
2026.10.01 20:45:03 japan [5M, 15M, 4H, no_signal=60, stale_candle=11, signal=1]
```

The start of the bracket lists the timeframes that were refreshed in that run, followed by skip-reason counters (only those above zero):

| Counter | Meaning |
|---|---|
| `no_data` | The symbol is missing from the downloaded data, or it is empty. |
| `unknown_suffix` | The ticker's suffix is not in the exchange list in `markets.py`. |
| `warmup` | Fewer than 60 candles on at least one timeframe. |
| `stale_candle` | The last 5M candle is older than 60 minutes (exchange closed or no fresh data). |
| `missing_value` | NaN in the 4H / VWAP / RSI / ATR / Bollinger value. |
| `no_signal` | Evaluated, but no valid setup or the score was too low. |
| `trend_filter` | Signal against a strong 4H trend with a low score. |
| `duplicate` | Same candle and direction. |
| `cooldown` | Same direction within the cooldown window. |
| `error` | An exception occurred for the symbol. |
| `signal` | A signal was found and queued. |

A failed or skipped run appears in the same log as an `error: <reason>` line: `no market argument provided`, `invalid market argument`, `watchlist is empty`, `locked, previous run still working`, or `failed to download data`. The scheduler also writes `ERROR: Exit code: <n>` when a scanner run ends abnormally, and `SLOW run: <n> s` for unusually slow runs.

**Error log:** `log/error_YYYY_MM_DD.log`, created only when an error occurred (with traceback). At most 3 per-symbol errors per run are written in detail. These never go to Telegram.

**Admin notification:** if `TELEGRAM_ADMIN_CHAT_ID` is set, a critical error or a download failure sends a private message (at most once per 30 minutes for the same error).

**Telegram statistics:** `log/telegram_count_YYYY_MM_DD.json` (daily and hourly message counts, all markets combined).

**Console output:** `log/scheduler.out` (from the cron line) keeps the console output: scanner start lines, data gap warnings, Telegram error codes, and calendar or watchlist warnings.

**Is it alive? A quick health check.**

- `ps aux | grep scheduler.py | grep -v grep` shows one running process.
- During market hours, the newest `log/YYYY_MM_DD.log` has fresh lines every five minutes (`tail -n 5 ~/rsi-scanner/log/$(ls -t ~/rsi-scanner/log | head -1)` is a simple way to look).
- Quiet logs on weekends, holidays, and outside market hours are normal.

## 3.13 Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `Missing secret: TELEGRAM_TOKEN` | The token is missing or written wrongly in `secrets.env`. Use `TELEGRAM_TOKEN=value` with no spaces and no quotes (section 3.5). |
| No alerts arrive, but the log shows `signal=` counts | Telegram delivery problem. Look in `log/scheduler.out` for `Telegram error`. Error 400 "chat not found": you have not pressed Start on your bot, or the chat ID in `RSI_search.py` is wrong (or still the example value). Error 401: the token is wrong. Error 403: you blocked the bot. Unsent alerts wait in `state/telegram_outbox.json`. |
| No alerts, and no `signal` counts anywhere | This can be normal, because the conditions are strict (section 2.3). Check that the scheduler is running and that the daily log is being written. |
| Nothing is running (`ps` shows no scheduler) | The cron line is missing or wrong. Check the absolute paths and `which flock`, then watch `log/scheduler.out`. |
| The cron line fails immediately | The `log/` folder does not exist yet (`mkdir -p log`), or the file permissions are wrong. |
| `ERROR: The scanner or the venv is missing.` | `RSI_search.py` or `venv/bin/python` is not where the scheduler expects it. The venv folder must be called `venv` and sit next to the scripts. |
| `ModuleNotFoundError` | A package is missing. Install it with the venv's pip: `venv/bin/pip install <package>`. |
| Many `no_data` for all markets | Yahoo is throttling your IP, yfinance is outdated, or the data is temporarily unavailable. Update yfinance (section 3.11), wait, and make sure you are not running a second copy from the same IP. |
| Many `no_data` for one market only | Wrong suffixes or changed ticker codes. Run `check_watchlists.py --yahoo`. |
| All `stale_candle` | Usually the exchange is closed (normal). If it happens during market hours, check Yahoo's delay, the other counters, and the server clock. |
| Many `warmup` | A new market that has not finished loading history, or a damaged cache. Pre-warm by hand (section 3.6), or delete `cache/<market>_*.pkl`. |
| `locked, previous run still working` | The earlier run was still busy. Occasional lines are normal. A stale lock from a crashed run is released automatically. |
| Frequent `SLOW run` lines, or runs stopped at 295 s | The server or the connection is too slow for the list size, or the markets overlap too much. Reduce the list sizes, or move to a stronger server. |
| `WARNING: <code> calendar unavailable` | `exchange_calendars` is not installed or does not know that calendar. Holidays are then not filtered (stale-data protection still works). |
| `WARNING: failed to reload watchlists.py` | A syntax error in your `watchlists.py`. Run `check_watchlists.py`. The old version stays in use until you fix it. |
| `check_watchlists.py` reports ❌ | Fix the line it names. A comment count that does not match the number of tickers is only a warning, but fix it too. |
| Alert times look wrong | Alert times are New York time by design, not your local time. Check that the server clock itself is correct. |

When you ask for help, send the relevant lines of the daily log and `log/scheduler.out`, and remove any text that looks like a bot token first (section 3.14).

## 3.14 Security and privacy

- **Keep the token secret.** Anyone with your bot token can send messages as your bot. Never post it, never email it, never commit it to a public repository, and never include it in a download. The project's download deliberately excludes `secrets.env`.
- **If you share a copy of the software,** remove your own chat ID first and never include `secrets.env`.
- **Install outside any web folder** (never in `public_html`) and run `chmod 600 secrets.env`.
- **Check logs before sharing them.** In some error situations, a network error message can contain the full Telegram web address, and that address includes your bot token. Before you send `log/scheduler.out` or any console output to anyone, search for `bot` followed by digits and a colon, and delete that part.
- **Secure the server itself.** Use SSH keys or strong passwords, keep the operating system updated, and do not run the screener as the root user.
- **No data is sent to me.** The screener has no telemetry. It communicates only with Yahoo Finance and Telegram (and with the Python package servers when you install or update packages).
- **Third-party terms.** You are responsible for using Yahoo data and Telegram in line with their terms (see the license). Yahoo's free data is generally meant for personal, non-commercial use (see section 2.7).

## 3.15 Uninstalling

1. Remove the cron line (cPanel: Cron Jobs → Delete; SSH: `crontab -e`), or disable the systemd service.
2. Run `pkill -f scheduler.py`.
3. Delete the folder: `rm -rf ~/rsi-scanner`.
4. Optional: revoke the bot token with `/revoke` at `@BotFather`, or delete the bot with `/deletebot`.

---

# Part 4: Support, custom work, and legal

## 4.1 Free support

Questions about installing, setting up, and using the screener are free. That includes help with the server requirements, the Telegram setup, the cron watchdog, reading the logs, understanding the alerts, and editing the watchlists. I answer them on a best-effort basis. I cannot promise a response time, and replies can take longer when I am busy or away.

**Contact:** support@finhavenarc.com
**Download:** [FinHavenArc Screener](#)

When you write to me, please include your operating system and Python version, what you did, what you expected, what happened, and the relevant log lines (with any bot token removed).

## 4.2 Custom work

Individually tailored work is possible on request, but it is not free. The screener is carefully balanced: the filtering conditions, the market schedules, the Yahoo limits, and the 2 × 250 rule all depend on one another. Examples of custom work:

- reprogramming the filtering conditions or the signal logic,
- building ticker lists based on criteria that you define,
- harmonizing several markets with the 2 × 250 rule and several other constraints at the same time,
- installing or administering a server for you.

Custom work is technical work on the software. It is not investment advice, and I do not recommend securities. Work like this takes several hours, so I cannot do it for free. Write to me with what you need, and I will tell you what it involves and what it costs, under a separate written agreement.

## 4.3 Important disclaimer: availability and data

**Please read this carefully. It is important.**

- **Yahoo data can be late.** Free Yahoo data can arrive with delays of 15–30 minutes or more on some exchanges, can be incomplete, wrong, or temporarily missing, and Yahoo can change or block access at any time without notice.
- **Servers and services can go down.** Your server, your internet connection, Yahoo, Telegram, or the Python libraries can fail, restart, or change. The cron watchdog restarts the scheduler automatically, but it cannot guarantee uninterrupted operation.
- **Alerts can be late, missing, duplicated, or wrong.** A missing alert is not a signal that nothing happened, and an alert is not a guarantee of anything.
- **I cannot give any guarantee.** I cannot promise that none of this will ever happen. In my own experience, the system is stable and data arrives continuously, and failures are rare. But they can happen, and I cannot take responsibility for them.
- **Never rely on the screener alone.** Verify prices and conditions in your broker or charting platform before you act, and never risk money that you cannot afford to lose.

The screener is information, not advice (see the box at the top of this guide).

## 4.4 License

FinHavenArc Screener is open source. It is provided under the FinHavenArc Screener Software License (included as `LICENSE.md` and also available [online](#)), which consists of the standard MIT License plus additional notices. In short, and without replacing the full text:

- You may use, copy, modify, merge, publish, distribute, sublicense, and sell the software, as long as the copyright and license notice stay with it.
- It is provided "as is", without warranty. The author is not liable for any claim or damage arising from its use.
- You are responsible for the software as you install, change, and run it, including any change made by you or by anyone from whom you obtained a modified copy. If a modified copy deletes your data, that is not the author's responsibility.
- The license covers only the software's own code. It gives no rights to Yahoo data or Telegram. Yahoo's free data is generally meant for personal, non-commercial use.
- It is not financial advice. You alone are responsible for your decisions.
- The name "FinHavenArc" is not licensed as a trademark. If you distribute a modified version, please say that it is modified.

Only the full text of `LICENSE.md` is legally binding.

---

# Appendix A: What changed since the previous guide

| Area | Before | Now |
|---|---|---|
| Name | RSI Scanner | FinHavenArc Screener is the official name. The scanner file is still `RSI_search.py`. Your cron line is not affected, because it starts `scheduler.py`. |
| Distribution | A service that I ran, with alerts for channel members | A free, open-source download with every file needed to run it, except `secrets.env`. Everyone runs their own copy. |
| Telegram target | Personal chat, then a channel (with `TELEGRAM_CHAT_IDS` and `TELEGRAM_THREAD_ID` for groups and topics) | Personal chat again. Group, channel, and topic delivery has been removed. |
| Chat ID | Fixed in the code (for the channel) | Every user sets their own personal chat ID in `RSI_search.py` (`TELEGRAM_CHAT_ID`). |
| secrets.env | `TELEGRAM_TOKEN` only | Still only `TELEGRAM_TOKEN`. Never part of the download. |
| Alert delivery | Individual messages | Batched: a queue emptied every 5 seconds, several alerts per message, outbox for failed messages. |
| Admin notifications | Described for a channel setup | Optional private message; error details are never sent as normal alerts. |
| Files | `markets.py`, `scheduler.py`, `RSI_search.py`, `watchlists.py`, `secrets.env` | The scanner file keeps its name, `RSI_search.py`. The other files are the same, plus `check_watchlists.py` (the watchlist checker) and `LICENSE.md`. |
| Watchlist comments | Free-form | A fixed pattern `# Country N (xx%)`: country, ticker count, and the 1-year target price figure. The checker verifies the count. |
| Language of the program | Console messages, log reasons, and code comments partly in Hungarian | Fully English. Log lines now read, for example, `error: watchlist is empty`, `ERROR: Exit code: <n>`, and `SLOW run: <n> s`. If you built your own scripts around the old log texts, update them. |
| London currency label | Alerts showed GBP for prices that are in pence | Alerts show GBX, which is correct for pence. |
| Operator guide | Short appendix | A full Part 3: server and resource requirements, step-by-step installation, Telegram setup, cPanel and cron watchdog, maintenance, monitoring, troubleshooting, and security. |
| Legal | Disclaimer | The MIT License plus additional notices, an explicit availability and data disclaimer, and a support and custom work policy. |

---

# Appendix B: Quick-start checklist

1. Get a Linux server where a process may run all day (a VPS is best), with Python 3.10 or newer.
2. Create `~/rsi-scanner` and upload the five program files.
3. `python3 -m venv venv`, then `venv/bin/pip install yfinance pandas numpy requests exchange_calendars tzdata`.
4. `mkdir -p cache state lock log`.
5. Create your Telegram bot with `@BotFather`, press Start on it, and find your chat ID.
6. Create `secrets.env` with `TELEGRAM_TOKEN=...`, then `chmod 600 secrets.env`. Enter your chat ID in `RSI_search.py` as `TELEGRAM_CHAT_ID`.
7. Run `venv/bin/python check_watchlists.py`.
8. Run `venv/bin/python RSI_search.py japan` once by hand, and pre-warm the other markets.
9. Add the cron line (section 3.7) in cPanel Cron Jobs or with `crontab -e`.
10. Check with `ps` and `tail` that the scheduler runs, and read section 4.3 once more.

---

*This guide is for informational purposes only and is not financial advice. See our [Financial Disclaimer](#) and [Privacy Policy](#).*
