# stupid_bot

## ema_bot (ema fast slow, cross strategy)

open futures order by cross signal between fast and slow indicator

## v1.4.12
- แสดง position เรียงตามกำไร
- mm profit จะปิด position จากกำไรน้อยไปมาก
- แสดงค่า Risk
- ตรวจสอบและแสดงรายการ order ที่เปิดไว้

## v1.4.11
- กำหนดรูปแบบการคำนวน MM PNL แบบ % (percent_mode = on)
- แยก loop ในการทำ MM ให้ทำงานไวขึ้น เพราะการปิด position ที่ราคาตลาด ทำให้เกิดผลต่างจากเวลา
- ปรับแก้ การแยกหรือรวม Margin Type ใหม่
- ปรับปรุง code เพิ่มเติม, แก้ปัญหาเรื่องทศนิยม
- ปรับปรุงการบันทีก log

## v1.4.10
- คำนวน amount, price แยกตาม precision ของแต่ล่ะเหรียญ
- กำหนด Margin Type แยกหรือรวมกันได้

## v1.4.9
- คำนวน Activation Price จาก SL (RR1 by @vaz)
- คำนวน Callback Rate จาก TP หรือ SL
- ปรับปรุง setting สำหรับ detect sideway

## v1.4.8
- detect sideway by ค่าเฉลี่ย high row (n periods) และ ATR 14
- เพิ่มการ confirm sideway ด้วย BBands และ MACD

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

    ;# จำนวนแท่งเทียนที่ต้องการให้บอทใช้ทำงาน
    ;CANDLE_LIMIT = 1000

    ;# จำนวนแท่งเทียนที่ต้องการแสดงกราฟ
    ;CANDLE_PLOT = 100

    ;# level การบันทึก log file ทั่วไปให้ใช้แบบ INFO
    ;# CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0
    LOG_LEVEL = 10

    ;# กำหนดรอบเวลาในแสดง update balancec และ mm check
    ;# 0=timeframe, 1=15, 2=20, 3=30, 4=60, 5=timeframe/2 
    UB_TIMER_MODE = 3

    ;# กำหนดเาลาเป็น นาที ถ้าเป็น 0 จะใช้ UB_TIMER_MODE
    MM_TIMER_MIN = 0.5

    ;# จำนวน TF ในการตรวจหา swing low/high
    ;SWING_TF = 5

    ;# จำนวนค่า swing low/high ที่ใช้ในการคิด SL
    ;SWING_TEST = 2

    ;# level ของ fibo ที่ใช้ในการคิด TP
    ;TP_FIBO = 2

    ;# คำนวน callback rate จาก 1 = TP, 2 = SL
    ;CB_AUTO_MODE = 1

    [setting]
    ;# 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    timeframe = 4h

    ;# กำหนดสัญญานที่แท่ง -1 หรือ -2 เท่านั้น, default = -2
    signal_index = -2

    ;# กำหนด Margin Type แยกหรือรวมกันได้
    ;# ต.ย. margin_type = USDT,BUSD
    margin_type = USDT

    ;# ระบุ symbol ที่ต้องการใน watch_list, back_list
    ;watch_list = BTCUSDT,BTCBUSD
    ;back_list = FTTUSDT,FTTBUSD

    ;# กำหนด on/off ในการเทรด
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

    ;# กำหนด on/off สำหรับ order TP LS
    tpsl_mode = on
    ;# กำหนดค่า TP/SL เป็น % จะคำนวนค่าจากราคาเหรียญ
    ;# ต้องให้คำนวน TP/SL auto ให้กำหนดค่า tp_long, tp_short, sl_long, sl_short เป็น 0.0 
    tp_long = 10.0
    tp_short = 10.0
    tp_close_long = 50.0
    tp_close_short = 50.0
    sl_long = 4.0
    sl_short = 4.0

    ;# กำหนด on/off สำหรับ trailing stop
    trailing_stop_mode = on

    ;# ค่า callback rate จะต้องอยู่ระหว่าง 0.1 ถึง 5.0, 0.0 for auto
    callback_long = 5.0
    callback_short = 5.0

    ;# ค่า active tl กำหนดเป็น % ถ้ากำหนดเป็น 0.0 เพื่อให้บอทคำนวนค่าให้
    ;# *** ถ้าพบปัญหาให้ตั้งค่าเป็น 0.0 ***
    active_tl_long = 10.0
    active_tl_short = 10.0

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
    ;# MACD, MACDs, MACDh
    ;confirm_macd_by = MACD
    ;# สำหรับคำนวน macd fast 12, slow 16, signal 9 คือค่ามาตราฐาน
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    ;# สำหรับคำนวน rsi, 14 คือค่ามาตราฐาน
    rsi_period = 14

    ;# กำหนด on/off สำหรับตรวจสอบ sideway
    detect_sideway = on
    ;# mode 1 = ATR 14 + AVG high row (n periods)
    ;# mode 2 = mode 1 + BBands + MACD histogram
    sideway_mode = 2
    ;# ค่าตัวคูณ ATR14 เพื่อกำหนด Upper และ Lower จากค่าเฉลี่ย
    atr_multiple = 1.5
    ;# จำนวน tf n แท่ง ที่ใช้คำนวน ค่าเฉลี่ยของ High, Low และ Bollinger Bands
    rolling_period = 15

    [symbols_setting]
    ;# กำหนดค่า setting แยกตามเหรียญ
    ;# ชื่อไฟล์ที่เก็บ setting ต้องเป็นไฟล์ csv, comment ถ้าต้องการปิดการทำงาน
    ; csv_name = symbol_config.csv

    [mm]
    ;# ต้องให้คำนวน TP/SL auto ให้กำหนดค่า tp_pnl_long, tp_pnl_short, sl_pnl_long, sl_pnl_short เป็น 0.0 
    ;# ค่าตัวแปรต่างๆ กำหนดค่าเป็น 0 หรือ comment ถ้าต้องการปิดการทำงาน

    ;# TP/SL แบบ PNL เพื่อปิด position โดยใช้ค่า PNL amount มาเป็นตัวกำหนด

    ;# ใส่ค่าเป็น amount (percent_mode=off) หรือ % (percent_mode=on) จะคำนวน amount ให้จาก % x cost_amount
    ;# ค่า close_rate ใส่เป็น % เท่านั้น
    ;# callback rate ranges from 0.1% to 5%, 0.0 for auto

    percent_mode = on

    ;# ส่วนนี้ใช้กับ long position
    tp_pnl_long = 0.30
    tp_pnl_close_rate_long = 25.0
    sl_pnl_long = 0.10
    ;# ค่า active tl ถ้ากำหนดเป็น 0.0 เพื่อให้บอทคำนวนค่าให้
    active_tl_pnl_long = 0.0
    callback_pnl_long = 5.0

    ;# ส่วนนี้ใช้กับ short position
    tp_pnl_short = 0.30
    tp_pnl_close_rate_short = 25.0
    sl_pnl_short = 0.10
    ;# ค่า active tl ถ้ากำหนดเป็น 0.0 เพื่อให้บอทคำนวนค่าให้
    active_tl_pnl_short = 0.0
    callback_pnl_short = 5.0

    ;# TP/SL Profit เพื่อปิด positions ทั้งหมด โดยใช้ค่าผลรวมของ profit มาเป็นตัวกำหนด 
    ;# จะทำจะงานตามรอบเวลาที่กำหนดไว้ที่ MM_TIMER_MIN
    
    ;# ส่วนนี้สำหรับคำนวนรวมทุก positions
    ;tp_profit = 1.5
    ;sl_profit = 1.4

    ;# ส่วนนี้สำหรับคำนวนแยก long position (ถ้ากำหนดแบบรวมไว้ ค่านี้จะไม่ถูกใช้)
    tp_profit_long = 3.0
    sl_profit_long = 1.5

    ;# ส่วนนี้สำหรับคำนวนแยก short position (ถ้ากำหนดแบบรวมไว้ ค่านี้จะไม่ถูกใช้)
    tp_profit_short = 3.0
    sl_profit_short = 1.5

    ;# กำหนดค่าการปิด position ที่มี margin น้อยกว่า clear_margin, default คีอ 0.01
    clear_margin = 0.01

    ;# ระบบจะนับ loss ถ้าเกิด loss เกิน loss_limit จะทำการเอาเหรียญออกจาก watch_list ชั่วคราว
    ;# เมื่อปิดเปิดบอทใหม่ watch_list จะเป็นค่าเดิมที่ตั้งไว้
    loss_limit = 0

# download

## v1.4.11
- https://mega.nz/file/2EZE2SqZ#fiLVqGJMNP7QmrWBEILPJffqaxhPsVWOX421eR__hLc

## v1.4.10 (bug)

## v1.4.9
- https://mega.nz/file/iFoRWCRC#_owOvvQPFemR1TZpb5yrH7jBB08ZFb3wXpdmkJzsAQ0

## v1.4.8
- https://mega.nz/file/DdRgnLID#bI-k7A7dlTkZIj3UE9-v0eBO7S6C4bdXyU_0VWgXch4

## v1.4.7 
- https://mega.nz/file/6IZQjDqL#H1kNAf6YO9IWuMc0nRv8BrDKtkmB_uiNU-TGE0lGP9w

# donate
- ETH: 0xeAfe7f1Db46E2c007b60174EB4527ab38bd54B54
- DOGE: DCkpCgt1HUVhCsvJVW7YA4E4NkxMsLHPz8
- BINANCE PAY:
![QR CODE](../app_binance.jpg)
