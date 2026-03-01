TICKERS = [
    "X:BTCUSD",
    "X:ETHUSD",
    "X:SOLUSD",
    "X:XRPUSD",
    "X:BNBUSD",
    "X:ADAUSD",
    "X:DOGEUSD",
    "X:AVAXUSD",
    "X:DOTUSD",
    "X:LINKUSD",
]

# OHLC bar settings
MULTIPLIER = 1
TIMESPAN = "minute"
LIMIT = 50_000

# Initial load window (days)
INITIAL_LOOKBACK_DAYS = 30

# Scheduler interval (seconds)
SYNC_INTERVAL_SECONDS = 90

# Rate-limit pause between tickers (seconds) — respects 5 req/min free tier
PAUSE_BETWEEN_TICKERS = 13

# Bulk insert chunk size
INSERT_CHUNK_SIZE = 3_000
