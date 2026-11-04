"""
THE SINGLE PLACE where you define the markets. Used by both scheduler.py and RSI_search.py.

Adding a new market:
  1) new exchange (if it doesn't exist yet)  -> one row in EXCHANGES (including suffixes)
  2) new runnable market                     -> one row in RUNS
  3) the watchlist in watchlists.py: <name>_watchlist_by_suffix
All times are LOCAL exchange time. The exchange is identified by the ticker's Yahoo suffix
(.T, .KS, .HK, .DE ...); a ticker without a suffix = USA.
"""
import os
import zoneinfo
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "log")
NY_TZ = zoneinfo.ZoneInfo("America/New_York")   # the ONLY displayed/logged clock

OPEN_DELAY = 5       # minutes after the open for the first scan
CLOSE_DELAY = 15     # minutes before the close for the last scan (no runs for that session afterwards)
WEEKDAYS = {1, 2, 3, 4, 5}


def _mins(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


# key, flag, currency, time zone, Yahoo suffixes, sessions
_EXCHANGES = [
    
("japan",          "🇯🇵", "JPY", "Asia/Tokyo",          ["T"],         ["09:00-11:30", "12:30-15:30"]),
("taiwan",         "🇹🇼", "TWD", "Asia/Taipei",         ["TW", "TWO"], ["09:00-13:30"]),
("hongkong",       "🇭🇰", "HKD", "Asia/Hong_Kong",      ["HK"],        ["09:30-12:00", "13:00-16:00"]),
("south_korea",    "🇰🇷", "KRW", "Asia/Seoul",          ["KS", "KQ"],  ["09:00-15:30"]),
("china",          "🇨🇳", "CNY", "Asia/Shanghai",       ["SS", "SZ"],  ["09:30-11:30", "13:00-15:00"]),
("australia",      "🇦🇺", "AUD", "Australia/Sydney",    ["AX"],        ["10:00-16:00"]),
("germany",        "🇩🇪", "EUR", "Europe/Berlin",       ["DE"],        ["09:00-17:30"]),
("united_kingdom", "🇬🇧", "GBP", "Europe/London",       ["L"],         ["08:00-16:30"]), # Yahoo quotes it in PENCE
("france",         "🇫🇷", "EUR", "Europe/Paris",        ["PA"],        ["09:00-17:30"]),
("spain",          "🇪🇸", "EUR", "Europe/Madrid",       ["MC"],        ["09:00-17:30"]),
("italy",          "🇮🇹", "EUR", "Europe/Rome",         ["MI"],        ["09:00-17:30"]),
("belgium",        "🇧🇪", "EUR", "Europe/Brussels",     ["BR"],        ["09:00-17:30"]),
("netherlands",    "🇳🇱", "EUR", "Europe/Amsterdam",    ["AS"],        ["09:00-17:30"]),
("denmark",        "🇩🇰", "DKK", "Europe/Copenhagen",   ["CO"],        ["09:00-17:00"]),
("sweden",         "🇸🇪", "SEK", "Europe/Stockholm",    ["ST"],        ["09:00-17:30"]),
("finland",        "🇫🇮", "EUR", "Europe/Helsinki",     ["HE"],        ["10:00-18:30"]),
("norway",         "🇳🇴", "NOK", "Europe/Oslo",         ["OL"],        ["09:00-16:20"]),
("hungary",        "🇭🇺", "HUF", "Europe/Budapest",     ["BD"],        ["09:00-17:00"]),
("austria",        "🇦🇹", "EUR", "Europe/Vienna",       ["VI"],        ["09:00-17:30"]),
("switzerland",    "🇨🇭", "CHF", "Europe/Zurich",       ["SW"],        ["09:00-17:30"]),
("turkey",         "🇹🇷", "TRY", "Europe/Istanbul",     ["IS"],        ["10:00-18:00"]),
("israel",         "🇮🇱", "ILS", "Asia/Jerusalem",      ["TA"],        ["09:59-17:14"]),
("greece",         "🇬🇷", "EUR", "Europe/Athens",       ["AT"],        ["10:00-17:20"]),
("poland",         "🇵🇱", "PLN", "Europe/Warsaw",       ["WA"],        ["09:00-17:00"]),
("canada",         "🇨🇦", "CAD", "America/Toronto",    ["TO","V","CN"],["09:30-16:00"]),
("united_states",  "🇺🇸", "USD", "America/New_York",    [],            ["09:30-16:00"]),
("united_states2", "🇺🇸", "USD", "America/New_York",    [],            ["09:30-16:00"]),
("mexico",         "🇲🇽", "MXN", "America/Mexico_City", ["MX"],        ["08:30-15:00"]),
("brazil",         "🇧🇷", "BRL", "America/Sao_Paulo",   ["SA"],        ["10:00-17:30"]),
]

EXCHANGES = {}
SUFFIX_MAP = {}
for _key, _flag, _ccy, _tz, _suffixes, _spans in _EXCHANGES:
    EXCHANGES[_key] = {
        "key": _key, "flag": _flag, "currency": _ccy, "tz": _tz,
        "sessions": [(_mins(a), _mins(b)) for a, b in (s.split("-") for s in _spans)],
    }
    for _s in _suffixes:
        SUFFIX_MAP[_s] = _key


def exchange_of(symbol):
    """The ticker's exchange based on its suffix (no suffix = USA). Unknown suffix -> None."""
    if "." not in symbol:
        return EXCHANGES["united_states"]
    key = SUFFIX_MAP.get(symbol.rsplit(".", 1)[1].upper())
    return EXCHANGES[key] if key else None


# The runnable markets (these are the scanner's arguments and the scheduler's scheduling units).
#   exchange  : whose exchange's time zone/sessions the scheduler schedules by
#   calendar  : exchange_calendars code (holidays); optional
#   watchlist : watchlists.py -> <watchlist>_watchlist_by_suffix
#   start     : optional, overrides the scheduled open (does NOT affect the VWAP/4H calculation)
RUNS = {
    "japan":           dict(label="🇯🇵 JAPAN",        exchange="japan",       calendar="XTKS",        watchlist="japan"),
    "taiwan":          dict(label="🇹🇼 TAIWAN",       exchange="taiwan",      calendar="XTAI",        watchlist="taiwan"),
    "hongkong":        dict(label="🇭🇰 HONG KONG",    exchange="hongkong",    calendar="XHKG",        watchlist="hongkong"),
    "south_korea":     dict(label="🇰🇷 SOUTH KOREA", exchange="south_korea", calendar="XKRX",        watchlist="south_korea"),
    "china":           dict(label="🇨🇳 CHINA",        exchange="china",       calendar="XSHG",       watchlist="china"),
    "australia":       dict(label="🇦🇺 AUSTRALIA",    exchange="australia",   calendar="XASX",        watchlist="australia"),
    "germany":         dict(label="🇩🇪 GERMANY",      exchange="germany",     calendar="XETR",      watchlist="germany"),
    "united_kingdom":  dict(label="🇬🇧 UNITED KINGDOM", exchange="united_kingdom", calendar="XLON",   watchlist="united_kingdom"),
    "france":          dict(label="🇫🇷 FRANCE",       exchange="france",      calendar="XPAR",      watchlist="france"),
    "spain":           dict(label="🇪🇸 SPAIN",        exchange="spain",       calendar="XMAD",      watchlist="spain"),
    "italy":           dict(label="🇮🇹 ITALY",        exchange="italy",       calendar="XMIL",      watchlist="italy"),
    "belgium":         dict(label="🇧🇪 BELGIUM",      exchange="belgium",     calendar="XBRU",      watchlist="belgium"),
    "netherlands":     dict(label="🇳🇱 NETHERLANDS",  exchange="netherlands", calendar="XAMS",      watchlist="netherlands"),
    "denmark":         dict(label="🇩🇰 DENMARK",      exchange="denmark",     calendar="XCSE",      watchlist="denmark"),
    "sweden":          dict(label="🇸🇪 SWEDEN",       exchange="sweden",      calendar="XSTO",      watchlist="sweden"),
    "finland":         dict(label="🇫🇮 FINLAND",      exchange="finland",     calendar="XHEL",      watchlist="finland"),
    "norway":          dict(label="🇳🇴 NORWAY",       exchange="norway",      calendar="XOSL",      watchlist="norway"),
    "hungary":         dict(label="🇭🇺 HUNGARY",      exchange="hungary",     calendar="XBUD",      watchlist="hungary"),
    "austria":         dict(label="🇦🇹 AUSTRIA",      exchange="austria",     calendar="XWBO",      watchlist="austria"),
    "switzerland":     dict(label="🇨🇭 SWITZERLAND",  exchange="switzerland", calendar="XSWX",      watchlist="switzerland"),
    "turkey":          dict(label="🇹🇷 TURKEY",       exchange="turkey",      calendar="XIST",      watchlist="turkey"),
    "israel":          dict(label="🇮🇱 ISRAEL",       exchange="israel",      calendar="XTAE",      watchlist="israel"),
    "greece":          dict(label="🇬🇷 GREECE",       exchange="greece",      calendar="ASEX",        watchlist="greece"),
    "poland":          dict(label="🇵🇱 POLAND",       exchange="poland",      calendar="XWAR",        watchlist="poland"),  
    "canada":          dict(label="🇨🇦 CANADA",         exchange="canada",        calendar="XTSE",        watchlist="canada"),
    "united_states":   dict(label="🇺🇸 UNITED STATES",  exchange="united_states", calendar="XNYS",   watchlist="united_states"),
    "united_states2":  dict(label="🇺🇸 UNITED STATES",  exchange="united_states", calendar="XNYS",   watchlist="united_states2", start="11:30"),
    "mexico":          dict(label="🇲🇽 MEXICO",         exchange="mexico",        calendar="XMEX",        watchlist="mexico"),
    "brazil":          dict(label="🇧🇷 BRAZIL",         exchange="brazil",        calendar="BVMF",         watchlist="brazil"),
}

# (Do NOT use "_" in the labels: Telegram Markdown would misinterpret it.)


def run_sessions(run):
    """Scheduling sessions in minutes: [(open, close), ...]"""
    sessions = EXCHANGES[run["exchange"]]["sessions"]
    if run.get("start"):
        sessions = [(_mins(run["start"]), sessions[-1][1])]
    return sessions


def write_log_line(market, text, when=None):
    """Daily run log: log/YYYY_MM_DD.log. Line: 'YYYY.MM.DD HH:MM:SS market [text]'."""
    when = when or datetime.now(NY_TZ)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        path = os.path.join(LOG_DIR, f"{when.strftime('%Y_%m_%d')}.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{when.strftime('%Y.%m.%d %H:%M:%S')} {market} [{text}]\n")
    except Exception as e:
        print(f"WARNING: failed to write to the log file: {e}")
