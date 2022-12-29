# stupid_bot

## ema_bot (ema fast slow, cross strategy)

open futures order by cross signal between fast and slow indicator

## v1.4.8
- detect sideway by ค่าเฉลี่ย high row (n periods) และ ATR 14

## v1.4.7
- เพิ่มการใช้ MACD ในการเปิด position
- คำนวนค่า take profit จาก fibo ของ max/min
- คำนวนค่า stop loss จาก swing low/high
- แจ้ง error ทาง line
- ปรับปรุง Active Price ของ Trailing Stop 
- ปรับปรุงการตรวจสอบชื่อเหรียญมีเครื่องหมาย _ (ขีดล่าง)
- แจ้งสรุป balance ตามรอบ timeframe

## v1.4.6
- ปรับการปิด position แบบ PNL ใหม่ โดยปรับไปใช้ TP/SL Order แทนการปิด position ด้วยบอท
- เพิ่ม sandbox mode สำหรับ https://testnet.binancefuture.com
- ปิด position + order ที่ initialMargin มีค่าน้อยกว่าหรือเท่ากับ 0.01
- รวมหรือแยก การนับ limit position ได้

## v1.4.5
- แยกนับ limit position ตาม direction (Long/Short)
- revise: log/notify, mm

## v1.4.4
- bug fix
- คำนวน profit แยก position direction (Long/Short) เพื่อใช้เปิด-ปิด position

## v1.4.3 beta
- เพิ่ม TP SL by PNL
- ตั้งเปิด-ปิด position ตาม profit
- limit loss ถ้าเกิน limit เอาออกจาก watch_list ไปก่อน จนกว่าจะ restart bot

## v1.4.2
- fix bug: แก้ปัญหาเปิด order เกิดจำนวน count trade
- new: เจัดเก็บ order history เตรียมใช้ตรวจสอบ win/loss
- new: ปรับการแสดงข้อมูล balance ให้มีรายละเอียดครบมากขึ้น
- ลบ order ที่ค้าง กรณีที่ position ถูกปิดไปแล้ว

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
    ;# กำหนดเป็น on เมื่อต้องการทดสอบด้วย https://testnet.binancefuture.com
    sandbox = off

    [line]
    notify_token = <line notify token>
    ;# กำหนด on/off เพื่อ เปิด/ปิด การลบรูปกราฟหลังจากใช้งานเสร็จ
    remove_plot = on
    ;# กำหนด on/off เพื่อ เปิด/ปิด การรายงานสรุป
    summary_report = on

    [app_config]
    ;TIME_SHIFT = 5
    ;CANDLE_LIMIT = 1000
    ;CANDLE_PLOT = 100
    ;# level การบันทึก log file ทั่วไปให้ใช้แบบ INFO
    ;# CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0
    LOG_LEVEL = 10
    ;# กำหนดรอบเวลาในแสดง update balancec และ mm check
    ;# 0=timeframe, 1=15, 2=20, 3=30, 4=60, 5=timeframe/2 
    UB_TIMER_MODE = 3
    ;# จำนวน TF ในการตรวจหา swing low/high
    ;SWING_TF = 5
    ;# จำนวนค่า swing low/high ที่ใช้ในการคิด SL
    ;SWING_TEST = 2
    ;# level ของ fibo ที่ใช้ในการคิด TP
    ;TP_FIBO = 2

    [setting]
    ;# 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    timeframe = 1m
    ;# กำหนดสัญญานที่แท่ง -1 หรือ -2 เท่านั้น, default = -2
    signal_index = -2
    margin_type = USDT

    ;# ระบุ symbol ที่ต้องการใน watch_list, back_list
    ;watch_list = BTCUSDT,DOGEUSDT,GALUSDT,GALAUSDT,IOSTUSDT,MANAUSDT,NEARUSDT,OCEANUSDT,XLMUSDT,XRPUSDT
    ;back_list = FTTUSDT

    trade_mode = on
    trade_long = on
    trade_short = on

    auto_max_leverage = off
    leverage = 20
    ;# กำหนดรูปการคิด cost # $ %
    cost_type = $
    cost_amount = 1.5

    ;# กำหนดจำนวน positions ทั้ง long, short รวมกันจะไม่เกิน limit_trade
    limit_trade = 10
    ;# ถ้ากำหนด limit_trade = 0 จะไปใช้ค่า limit_trade_long และ limit_trade_short แทน
    ;# กำหนดจำนวน positions แยกตาม long, short จะไม่เกิน limit_trade_long และ limit_trade_short
    limit_trade_long = 5
    limit_trade_short = 5

    ;# กำหนดจำนวน balance ขั้นต่ำ จะไม่เปิด position ใหม่ ถ้า balance เหลือต่ำกว่า not_trade
    not_trade = 10.0

    tpsl_mode = on
    ;# ต้องให้คำนวน TP/SL auto ให้กำหนดค่า tp_long, tp_short, sl_long, sl_short เป็น 0.0 
    tp_long = 10.0
    tp_short = 10.0
    tp_close_long = 50.0
    tp_close_short = 50.0
    sl_long = 4.0
    sl_short = 4.0

    ;# กำหนด on/off สำหรับ trailing stop
    trailing_stop_mode = on
    ;# ค่า callback rate จะต้องอยู่ระหว่าง 0.1 ถึง 5.0
    callback_long = 5.0
    callback_short = 5.0
    ;# ค่า active tl มีปัญหา ให้กำหนดเป็น 0.0 เพื่อให้ API กำหนด auto จะเป็นราคาใกล้ๆราคาตลาด
    active_tl_long = 0.0
    active_tl_short = 0.0

    ;# กำหนดค่า fast, mid, slow เพื่อให้บอทใช้หาสัญญานในการเปิด position
    ;# ระบุ type fast,slow => EMA, SMA, HMA, RMA, WMA, VWMA
    fast_type = EMA
    fast_value = 8
    mid_type = EMA
    mid_value = 34
    slow_type = EMA
    slow_value = 34

    ;# กำหนด on/off สำหรับตรวจสอบ macd ก่อนเปิด position
    confirm_macd_mode = on
    ;# สำหรับคำนวน macd fast 12, slow 16, signal 9 คือค่ามาตราฐาน
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    ;# สำหรับคำนวน rsi, 14 คือค่ามาตราฐาน
    rsi_period = 14

    detect_sideway = on
    atr_multiple = 1.5
    rolling_period = 15

    [symbols_setting]
    ;# กำหนดค่า setting แยกตามเหรียญ
    ;# ชื่อไฟล์ที่เก็บ setting ต้องเป็นไฟล์ csv, comment ถ้าต้องการปิดการทำงาน
    ; csv_name = symbol_config.csv

    [mm]
    ;# ต้องให้คำนวน TP/SL auto ให้กำหนดค่า tp_pnl_long, tp_pnl_short, sl_pnl_long, sl_pnl_short เป็น 0.0 
    ;# ค่าตัวแปรต่างๆ กำหนดค่าเป็น 0 หรือ comment ถ้าต้องการปิดการทำงาน

    ;# ตั้ง TP/SL เพื่อปิด position โดยใช้ค่า PNL amount มาเป็นตัวกำหนด
    ;# ใส่ค่าเป็น amount, เฉพาะ close_rate ใส่เป็น %
    ;# ใช้กับ long position
    tp_pnl_long = 0.30
    tp_pnl_close_rate_long = 25.0
    sl_pnl_long = 0.10
    ;# ค่า active tl มีปัญหา ให้กำหนดเป็น 0.0 เพื่อให้ API กำหนด auto จะเป็นราคาใกล้ๆราคาตลาด
    active_tl_pnl_long = 0.0
    callback_pnl_long = 5.0
    ;# ใช้กับ short position
    tp_pnl_short = 0.30
    tp_pnl_close_rate_short = 25.0
    sl_pnl_short = 0.10
    ;# ค่า active tl มีปัญหา ให้กำหนดเป็น 0.0 เพื่อให้ API กำหนด auto จะเป็นราคาใกล้ๆราคาตลาด
    active_tl_pnl_short = 0.0
    callback_pnl_short = 5.0

    ;# TP/SL เพื่อปิด positions ทั้งหมด โดยใช้ค่าผลรวมของ profit มาเป็นตัวกำหนด โดยบอทจะทำ TP/SL ตามรอบเวลาที่กำหนดไว้ (default 60 secs)
    ;# ใช้กับทุก positions
    ;tp_profit = 1.5
    ;sl_profit = 1.4
    ;# ใช้กับ long position (ถ้ากำหนดแบบรวมไว้ ค่านี้จะไม่ถูกใช้)
    tp_profit_long = 3.0
    sl_profit_long = 1.5
    ;# ใช้กับ short position (ถ้ากำหนดแบบรวมไว้ ค่านี้จะไม่ถูกใช้)
    tp_profit_short = 3.0
    sl_profit_short = 1.5

    ;# ระบบจะนับ loss ถ้าเกิด loss เกิน loss_limit จะทำการเอาเหรียญออกจาก watch_list ชั่วคราว
    ;# เมื่อปิดเปิดบอทใหม่ watch_list จะเป็นค่าเดิมที่ตั้งไว้
    loss_limit = 0

# download

## v1.4.8 (testing)
- https://mega.nz/file/fdwjGQxR#IHTb4o7xvxfcB-shTe6iwbQqe2CUofanPVTpzWxHNAE

## v1.4.7 
- https://mega.nz/file/6IZQjDqL#H1kNAf6YO9IWuMc0nRv8BrDKtkmB_uiNU-TGE0lGP9w

# donate
- ETH: 0xeAfe7f1Db46E2c007b60174EB4527ab38bd54B54
- DOGE: DCkpCgt1HUVhCsvJVW7YA4E4NkxMsLHPz8