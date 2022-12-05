# stupid_bot

## adxrsi_bot (adx rsi strategy)

open futures order by ADX+RSI indicator

## v1.1.2
- แยกนับ limit position ตาม direction (Long/Short)
- revise: log/notify, mm

## v1.1.1
- เพิ่ม TP SL by PNL
- ตั้งเปิด-ปิด position ตาม profit
- limit loss ถ้าเกิน limit เอาออกจาก watch_list ไปก่อน จนกว่าจะ restart bot
- คำนวน profit แยก position direction (Long/Short) เพื่อใช้เปิด-ปิด position

## v1.1
- revise ADX,RSI signal for Enter/Exit

## v1.0
- capture trading signal by ADX+RSI indacator
- code from ema_bot structure

## config.ini (rename จาก config.ini.sample)

    [binance]
    api_key = <binance api key>
    api_secret = <binance app secret>

    [line]
    notify_token = <line notify token>

    [setting]
    ; 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    timeframe = 15m
    ; กำหนดสัญญานที่แท่ง -1 หรือ -2 เท่านั้น, default = -1
    signal_index = -1
    margin_type = USDT

    ; ระบุ symbol ที่ต้องการใน watch_list, back_list
    ; watch_list = BTCUSDT,DOGEUSDT,GALUSDT,GALAUSDT,IOSTUSDT,MANAUSDT,NEARUSDT,OCEANUSDT,XLMUSDT,XRPUSDT
    ; back_list = FTTUSDT

    trade_mode = on
    trade_long = on
    trade_short = on

    auto_max_leverage = off
    leverage = 20
    ; กำหนดรูปการคิด cost # $ %
    cost_type = $
    cost_amount = 1.5

    ; กำหนดจำนวน positions แยกตาม long, short จะไม่เกิน limit_trade_long และ limit_trade_short
    limit_trade_long = 5
    limit_trade_short = 5
    ; กำหนดจำนวน balance ขั้นต่ำ จะไม่เปิด position ใหม่ ถ้า balance เหลือต่ำกว่า not_trade
    not_trade = 10.0

    tpsl_mode = on
    tp_long = 10.0
    tp_short = 10.0
    tp_close_long = 50.0
    tp_close_short = 50.0
    sl_long = 4.0
    sl_short = 4.0

    trailing_stop_mode = on
    callback_long = 5.0
    callback_short = 5.0
    active_tl_long = 10.0
    active_tl_short = 10.0

    adx_period = 14
    adx_in = 25
    position_ob = 70
    position_os = 30
    exit_ob = 50
    exit_os = 50

    ; สำหรับคำนวน macd, default คือค่ามาตราฐาน
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    ; สำหรับคำนวน rsi, default คือค่ามาตราฐาน
    rsi_period = 14

    ; กำหนดค่า setting แยกตาม symbol
    [symbols_setting]
    ; ชื่อไฟล์ที่เก็บ setting ต้องเป็นไฟล์ csv
    csv_name = symbol_config.csv

    [mm]
    ; take profit if PNL gather than tp_if_pnl_gt, 0 = not active
    tp_if_pnl_gt = 0.0
    ; stop loss if PNL less than sl_if_pnl_lt, 0 = not active
    sl_if_pnl_lt = -0.0

    ; take profit if all Profit gather than tp_if_all_profit_gt, 0 = not active
    tp_if_all_profit_gt = 0.0
    ; stop loss if all Profit less than sl_if_all_profit_lt, 0 = not active
    sl_if_all_profit_lt = -0.0

    ; take profit if all Long Profit gather than tp_if_long_profit_gt, 0 = not active
    tp_if_long_profit_gt = 2.5
    ; stop loss if all Long Profit less than sl_if_long_profit_lt, 0 = not active
    sl_if_long_profit_lt = -2.5

    ; take profit if all Short Profit gather than tp_if_short_profit_gt, 0 = not active
    tp_if_short_profit_gt = 2.5
    ; take profit if all Short Profit gather than sl_if_short_profit_lt, 0 = not active
    sl_if_short_profit_lt = -2.5

    ; loss counter, move symbol out of wishlists if more then loss_limit, 0 = not active
    ; reset loss counter by restart bot
    loss_limit = 0

## donate
- ETH: 0xeAfe7f1Db46E2c007b60174EB4527ab38bd54B54
- DOGE: DCkpCgt1HUVhCsvJVW7YA4E4NkxMsLHPz8