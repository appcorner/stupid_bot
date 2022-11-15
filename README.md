# stupid_bot

## binance_bot (mao bot strategy)

uses binance_bot for testing, make a mao bot strategy (ema+macd), capture signal and send line notify

    cd binance_bot

## pip

    pip install python-binance
    pip install mplfinance

## config.ini (rename จาก config.ini.sample)

    [binance]
    api_key = <binance api key>
    api_secret = <binance app secret>

    [bitkub]
    # การเชื่อมต่อไป bitkub (อยู่ระหว่างการพัฒนา)
    api_key = <bitkub api key>
    api_secret = <bitkub app secret>

    [line]
    notify_token = <line notify token>

    [ema_macd]
    # only bitkub lists
    watch_list = 1INCHUSDT,AAVEUSDT,ADAUSDT,ALGOUSDT,ALPHAUSDT,APEUSDT,ATOMUSDT,AVAXUSDT,AXSUSDT,BALUSDT,BANDUSDT,BATUSDT,BCHUSDT,BNBUSDT,BTCUSDT,CELOUSDT,CHZUSDT,COMPUSDT,CRVUSDT,CVCUSDT,DOGEUSDT,DOTUSDT,DYDXUSDT,ENJUSDT,ENSUSDT,ETHUSDT,FTMUSDT,FTTUSDT,GALUSDT,GALAUSDT,GRTUSDT,HBARUSDT,IMXUSDT,IOSTUSDT,KNCUSDT,KSMUSDT,LINKUSDT,LRCUSDT,MANAUSDT,MATICUSDT,MKRUSDT,NEARUSDT,OCEANUSDT,OMGUSDT,OPUSDT,SANDUSDT,SNXUSDT,SOLUSDT,SUSHIUSDT,TRXUSDT,UNIUSDT,XLMUSDT,XRPUSDT,XTZUSDT,YFIUSDT,ZILUSDT,ZRXUSDT

    # ค่าที่ใช้ในการคำนวนสัญญาน
    ema_base = 35
    ema_fast = 8
    ema_slow = 32
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9

    # จำนวนวันย้อนหลัง สำหรับใช้ตรวจสัญญาน
    back_days = 3 

    # รูปแบบ timeframe 1m, 5m, 15m, 1h, 4h, 1d
    candle_timeframe = 15m
    # จำนวน timeframe ที่แสดงใน plot
    candle_max_record = 100

## create folder (if not exist) -> plots

    mkdir plots

## run bot

    python maobot.py