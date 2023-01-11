# stupid_bot

## adxrsi_bot (adx rsi strategy)

open futures order by ADX+RSI indicator

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
    ;CANDLE_LIMIT = 1000
    ;CANDLE_PLOT = 100
    ;# level การบันทึก log file ทั่วไปให้ใช้แบบ INFO
    ;# CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0
    LOG_LEVEL = 20
    ;# กำหนดรอบเวลาในแสดง update balancec และ mm check
    ;# 0=timeframe, 1=15, 2=20, 3=30, 4=60, 5=timeframe/2 
    UB_TIMER_MODE = 3
    ;# จำนวน TF ในการตรวจหา swing low/high
    ;SWING_TF = 5
    ;# จำนวนค่า swing low/high ที่ใช้ในการคิด SL
    ;SWING_TEST = 2
    ;# level ของ fibo ที่ใช้ในการคิด TP
    ;TP_FIBO = 2
    ;# คำนวน callback rate จาก 1 = TP, 2 = SL
    ;CB_AUTO_MODE = 1

    [setting]
    ; 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    timeframe = 15m
    ; กำหนดสัญญานที่แท่ง -1 หรือ -2 เท่านั้น, default = -1
    signal_index = -1
    margin_type = USDT

    ;# ระบุ symbol ที่ต้องการใน watch_list, back_list
    ;watch_list = BTCUSDT,DOGEUSDT,GALUSDT,GALAUSDT,IOSTUSDT,MANAUSDT,NEARUSDT,OCEANUSDT,XLMUSDT,XRPUSDT
    ;back_list = FTTUSDT

    trade_mode = on
    trade_long = on
    trade_short = on

    auto_max_leverage = off
    leverage = 20
    ; กำหนดรูปการคิด cost # $ %
    cost_type = $
    cost_amount = 1.5

    ;# กำหนดจำนวน positions ทั้ง long, short รวมกันจะไม่เกิน limit_trade
    limit_trade = 10
    ;# ถ้ากำหนด limit_trade = 0 จะไปใช้ค่า limit_trade_long และ limit_trade_short แทน
    ;# กำหนดจำนวน positions แยกตาม long, short จะไม่เกิน limit_trade_long และ limit_trade_short
    limit_trade_long = 5
    limit_trade_short = 5

    ; กำหนดจำนวน balance ขั้นต่ำ จะไม่เปิด position ใหม่ ถ้า balance เหลือต่ำกว่า not_trade
    not_trade = 10.0

    ;# กำหนด on/off สำหรับ TP/SL
    tpsl_mode = on
    ;# ต้องการให้คำนวน TP/SL auto ให้กำหนดค่า tp_long, tp_short, sl_long, sl_short เป็น 0.0 
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
    ;# ค่า active tl ถ้ามีปัญหา ให้กำหนดเป็น 0.0 เพื่อให้ API คำนวน auto
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
    sto_mode = 'off'
    sto_enter_long = 20
    sto_enter_short = 80

    ; กำหนดค่า setting แยกตาม symbol
    [symbols_setting]
    ; ชื่อไฟล์ที่เก็บ setting ต้องเป็นไฟล์ csv
    csv_name = symbol_config.csv

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

    ;# ปิด position + order ที่ initialMargin มีค่าน้อยกว่าหรือเท่ากับ clear_margin
    clear_margin = 0.01

    ;# ระบบจะนับ loss ถ้าเกิด loss เกิน loss_limit จะทำการเอาเหรียญออกจาก watch_list ชั่วคราว
    ;# เมื่อปิดเปิดบอทใหม่ watch_list จะเป็นค่าเดิมที่ตั้งไว้
    ;# 0 = ปิดการใช้งาน
    loss_limit = 0

## donate
- ETH: 0xeAfe7f1Db46E2c007b60174EB4527ab38bd54B54
- DOGE: DCkpCgt1HUVhCsvJVW7YA4E4NkxMsLHPz8