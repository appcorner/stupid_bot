# stupid_bot

## ema_bot (ema fast slow, cross strategy)

open futures order by cross signal between fast and slow indicator

## v1.4.1
- fix bug: ปัญหาการ set_leverage, ลำดับการทำงานการอ่าน multiple setting ต้องทำก่อนการ set_leverage

## v1.4
- เปลี่ยนวิธีการเรียกใช้ exchange api
- ปรับการแสดง position & balance
- เพิ่มการเขียน log
- แก้ last price ในการคำนวน amount เอาราคาล่าสุด
- ~~เพิ่มรูปแบบการคำนวน amount แบบ 'M' คำนวนจาก minAmount => amount = priceEntry * minAmount / leverage~~
- กรณี TF >= 4h ให้เปิด trade ตามสัญญาน ณ.ตอนที่เปิดใช้งาน (กรณี TF ต่ำกว่า จะรอ trade รอบเวลาถัดไป)
- ปรับ config.ini แยก long short 
- กำหนดค่า setting แยกตาม symbol 

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

    trade_mode = on
    trade_long = on
    trade_short = on

    auto_max_leverage = off
    leverage = 20
    ; กำหนดรูปการคิด cost # $ %
    cost_type = $
    cost_amount = 1.5

    ; กำหนดจำนวน positions จะไม่เกิน limit_trade
    limit_trade = 10
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

    ; ระบุ type fast,slow => EMA, SMA, HMA, RMA, WMA, VWMA
    fast_type = EMA
    fast_value = 8
    mid_type = EMA
    mid_value = 34
    slow_type = EMA
    slow_value = 34

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

## donate
- ETH: 0xeAfe7f1Db46E2c007b60174EB4527ab38bd54B54
- DOGE: DCkpCgt1HUVhCsvJVW7YA4E4NkxMsLHPz8