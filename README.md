# stupid_bot

## pip

    pip install python-binance
    pip install mplfinance

## setting config.py

    API_KEY = '<binance api key>'
    API_SECRET = '<binance app secret>'
    LINE_NOTIFY_TOKEN = '<line notify token>'

## config maobot -> stupid\strategy\ema_macd.py

    # ค่าที่ใช้ในการคำนวนสัญญาน
    EMA_BASE = 35
    EMA_FAST = 8
    EMA_SLOW = 32
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9

    BACK_DAYS = 7 # จำนวนวันย้อนหลัง สำหรับใช้ตรวจสัญญาน

    CANDLE_TIMEFRAME = '15m' # รูปแบบ timeframe 15m, 4h, 1d
    CANDLE_MAX_RECORD = 100 # จำนวน timeframe ที่กำหนดใน plot

## run bot

    python maobot.py