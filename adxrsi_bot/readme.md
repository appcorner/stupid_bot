# stupid_bot

## adxrsi_bot (adx rsi strategy)

open futures order by ADX+RSI[+STO] indicator

## disclaimer (ข้อจำกัดความรับผิดชอบ)
- ผู้พัฒนาไม่สามารถรับผิดชอบ ความเสียหายที่เกิดจาก การใช้งาน บัค error หรือ อื่นๆ ได้ ผู้ใช้โปรแกรมต้องยอมรับความเสี่ยงที่เกิดขึ้นเอง โดย ทดลอง ทดสอบ ให้มั่นใจก่อนนำไปใช้ในการลงทุน
- ผู้พัฒนาไม่อนุญาติให้นำโปรแกรมไปแสวงหาผลประโยชน์จากบุคคลอื่น หากทราบ จะหยุดการพัฒนาและเผยแพร่โปรแกรมโดยทันที

## V1.5.2b (ปรับเท่า EMA)
- ปรับปรุง code เพื่อลดปัญหา timestamp

## V1.5.2 (ปรับเท่า EMA)
- แก้ปัญหาการ set auto leverage
- ตรวจสอบปัญหาจากการทำงาน api balance
- ปรับปรุง code ให้ดีขึ้น ได้แก่ การตรวจสอบ risk, cancel orders, order history
- แก้ปัญหาอื่นๆที่พบ ได้แก่ order history, order ใน hedge mode

## V1.5.1 (ปรับเท่า EMA)
- ปรับปรุงการเปิด position และ order ให้ตรงกับ position mode
- เพิ่มสามารถเปิด position และ order แบบ hedge
- ปรับปรุงการจัดเก็บ orders history ใหม่ เพื่อรองรับ multi timeframe และ adaptive trailing
- ปรับแก้การเลือกเหรียญ future ด้วยข้อมูลจาก settle ที่ตรงกับ margin type (มีการปรับโครงสร้างข้อมูลจาก api fetch_markets ใหม่)
- ปรับการแจ้งเตือน error ทาง line เป็น error แรก และ error สุดท้าย ในการทำงานของแต่ละรอบ
- กำหนด setting ในการเลือก clear order ที่ไม่มี postion ([app_config]CLEAR_OLD_ORDER) ในตอนเริ่มการทำงานครั้งแรก
- ทดลองการเทรดในช่วง sideway โดยเปิด position แบบ hedge ([hedge]sideway_trade) ใช้ค่า TP SL TL ใน config
- แก้ Bug การแปลงจำนวนหลักพัน

## v1.1.5
- แสดง position เรียงตามกำไร
- mm profit จะปิด position จากกำไรน้อยไปมาก
- แสดงค่า Risk
- ตรวจสอบและแสดงรายการ order ที่เปิดไว้

## v1.1.4
- กำหนดรูปแบบการคำนวน MM PNL แบบ % (percent_mode = on)
- แยก loop ในการทำ MM ให้ทำงานไวขึ้น เพราะการปิด position ที่ราคาตลาด ทำให้เกิดผลต่างจากเวลา
- การแยกหรือรวม Margin Type
- ปรับปรุง code เพิ่มเติม, แก้ปัญหาเรื่องทศนิยม
- ปรับปรุงการบันทีก log

## v1.1.3
- เพิ่ม STO (Stochastic Oscillator)
- ปิด PNL position ด้วย TP/SL Order แทนการปิด position ด้วยบอท โดยคำนวนค่าจาก [mm] PNL ที่ตั้ง (จาก setting ที่เป็น %)
- เพิ่ม sandbox mode สำหรับ https://testnet.binancefuture.com
- ปิด position + order ที่ initialMargin มีค่าน้อยกว่าหรือเท่ากับ 0.01 (เปลี่ยนค่า clear_margin ใน [mm] ได้)
- รวมการนับ limit position หรือแยก Long/Short position
- การคำนวน take profit จาก fibo ของ max/min
- การคำนวน stop loss จาก swing low/high
- การคำนวน Activation Price จาก SL (RR1 by @vaz)
- การคำนวน Callback Rate จาก TP หรือ SL
- แจ้ง error ทาง line
- ปรับปรุง Active Price ของ Trailing Stop
- ไม่ใช้เหรียญมีเครื่องหมาย _ (ขีดล่าง) จาก api fetch_markets
- แจ้งสรุป balance ตามรอบ timeframe

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

    ;# กำหนด timeframe ขั้นต่ำ ที่ต้องการเทรดเมื่อเริ่มการทำงานครั้งแรก (default = 4h)
    ;START_TRADE_TF = 1h

    ;# กำหนด on/off ในการเลือก clear order ที่ไม่มี postion ในตอนเริ่มการทำงานครั้งแรก
    ;CLEAR_OLD_ORDER = off

    [setting]
    ;# 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    timeframe = 4h

    ;# กำหนดสัญญานที่แท่ง -1 หรือ -2 เท่านั้น, default = -2
    signal_index = -2

    ;# กำหนด Margin Type แยกหรือรวมกันได้
    ;# ต.ย. margin_type = USDT,BUSD
    margin_type = USDT

    ;# กำหนดเลข magic number เพื่อระบุใน order id ไม่เกิน 10 อักษร
    magic_number = 99999

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

    ;# default period
    adx_period = 14
    rsi_period = 14
    sto_k_period = 14
    sto_smooth_k = 3
    sto_d_period = 3

    ;# basic setting
    adx_in = 12
    position_long = up
    position_value_long = 70
    position_short = down
    position_value_short = 30
    exit_long = down
    exit_value_long = 50
    exit_short = up
    exit_value_short = 50

    ;# STO on/off
    sto_mode = off
    sto_enter_long = 20
    sto_enter_short = 80

    [hedge]
    ;# กำหนด on เพื่อเปิด position แบบ hedge
    hedge_trade = off

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

## v1.5.2b
- https://mega.nz/file/yFRRFCqA#7uoQXyaD50HDonS1VK7saC3qE1jUhNzGPM2WMcclkeY

## v1.5.2
- https://mega.nz/file/3VYB2RAC#I04Y-A2PGIGItLXqSN4eq5_CmxPBFtEeBeTwUgh7JKo

## v1.1.4
- https://mega.nz/file/7BpghRBQ#rk8YsEqTwwWdjbr4B8_TqdrpccdmGNVwzDLu3qFo7OA

## v1.1.3
- https://mega.nz/file/Pc4wFThI#cgwS7vmO9FcNOSjVJhhKUbGDvR6zB95FAJSIvgNmENI

# donate
- ETH: 0xeAfe7f1Db46E2c007b60174EB4527ab38bd54B54
- DOGE: DCkpCgt1HUVhCsvJVW7YA4E4NkxMsLHPz8
- BINANCE PAY:
# ![QR CODE](../app_binance.jpg)