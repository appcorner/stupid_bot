# stupid_bot

## ema_bot (ema fast slow, cross strategy)

open futures order by cross signel between fast and slow indicator

## config.ini (rename จาก config.ini.sample)

    [binance]
    api_key = <binance api key>
    api_secret = <binance app secret>

    [line]
    notify_token = <line notify token>

    [setting]
    ; 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    timeframe = 1m
    ; กำหนดสัญญานที่แท่ง -1 หรือ -2 เท่านั้น, default = -2
    signal_index = -2
    margin_type = USDT

    ; ระบุ symbol ที่ต้องการใน watch_list, back_list
    ; watch_list = BTCUSDT,DOGEUSDT,GALUSDT,GALAUSDT,IOSTUSDT,MANAUSDT,NEARUSDT,OCEANUSDT,XLMUSDT,XRPUSDT
    ; back_list = FTTUSDT

    trade_mode = off
    trade_long = on
    trade_short = on
    auto_max_leverage = off
    leverage = 20
    cost_type = $
    cost_amount = 1.5
    limit_trade = 5
    not_trade = 10
    tpsl_mode = on
    tp_rate = 10
    tp_close = 50
    sl_rate = 4
    trailing_stop_mode = on
    callback = 5
    active_tl_rate = 10

    ; ระบุ type fast,slow => EMA, SMA, HMA, RMA, WMA, VWMA
    fast_type = EMA
    fast_value = 8
    mid_type = EMA
    mid_value = 34
    slow_type = EMA
    slow_value = 34
