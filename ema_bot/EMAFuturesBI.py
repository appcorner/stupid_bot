from asyncio import get_event_loop, gather, sleep
import pandas as pd
import pandas_ta as ta
import time
import mplfinance as mpf 
from LineNotify import LineNotify
import config
import os
import pathlib
import logging
from logging.handlers import RotatingFileHandler

# -----------------------------------------------------------------------------
# API_KEY, API_SECRET, LINE_NOTIFY_TOKEN in config.ini
# -----------------------------------------------------------------------------

import ccxt.async_support as ccxt

# print('CCXT Version:', ccxt.__version__)
# -----------------------------------------------------------------------------

bot_name = 'EMA Futures Binance, version 1.4'

# ansi escape code
CLS_SCREEN = '\033[2J\033[1;1H' # cls + set top left
CLS_LINE = '\033[0J'
SHOW_CURSOR = '\033[?25h'
HIDE_CURSOR = '\033[?25l'
CRED  = '\33[31m'
CGREEN  = '\33[32m'
CYELLOW  = '\33[33m'
CEND = '\033[0m'
CBOLD = '\33[1m'

# กำหนดเวลาที่ต้องการเลื่อนการอ่านข้อมูล เป็นจำนวนวินาที
TIME_SHIFT = 5

TIMEFRAME_SECONDS = {
    '1m': 60,
    '3m': 60*3,
    '5m': 60*5,
    '15m': 60*15,
    '30m': 60*30,
    '1h': 60*60,
    '2h': 60*60*2,
    '4h': 60*60*4,
    '6h': 60*60*6,
    '8h': 60*60*8,
    '12h': 60*60*12,
    '1d': 60*60*24,
}

CANDLE_LIMIT = 1000
CANDLE_PLOT = 100

# ----------------------------------------------------------------------------
# global variable
# ----------------------------------------------------------------------------
notify = LineNotify(config.LINE_NOTIFY_TOKEN)

logger = logging.getLogger("App Log")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = RotatingFileHandler('app.log', maxBytes=200000, backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)

all_positions = pd.DataFrame(columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide", "initialMargin"])
count_trade = 0

start_balance_entry = 0.0
balance_entry = 0.0

watch_list = {}
all_symbols = {}
all_leverage = {}
all_candles = {}

RSI30 = [30 for i in range(0, CANDLE_PLOT)]
RSI50 = [50 for i in range(0, CANDLE_PLOT)]
RSI70 = [70 for i in range(0, CANDLE_PLOT)]

CSV_COLUMNS = [
        "symbol",
        "signal_index",
        "margin_type",
        "trade_mode",
        "trade_long",
        "trade_short",
        "leverage",
        "cost_type",
        "cost_amount",
        "tpsl_mode",
        "tp_long",
        "tp_short",
        "tp_close_long",
        "tp_close_short",
        "sl_long",
        "sl_short",
        "trailing_stop_mode",
        "callback_long",
        "callback_short",
        "active_tl_long",
        "active_tl_short",
        "fast_type",
        "fast_value",
        "mid_type",
        "mid_value",
        "slow_type",
        "slow_value"
        ]
symbols_setting = pd.DataFrame(columns=CSV_COLUMNS)

async def line_chart(symbol, df, msg=''):
    data = df.tail(CANDLE_PLOT)

    colors = ['green' if value >= 0 else 'red' for value in data['MACD']]
    added_plots = [
        mpf.make_addplot(data['fast'],color='red',width=0.5),
        mpf.make_addplot(data['mid'],color='orange',width=0.5),
        mpf.make_addplot(data['slow'],color='green',width=0.5),
        mpf.make_addplot(data['RSI'],ylim=(10, 90),panel=2,color='blue',width=0.75),
        mpf.make_addplot(RSI30,ylim=(10, 90),panel=2,color='red',linestyle='-.',width=0.5),
        mpf.make_addplot(RSI50,ylim=(10, 90),panel=2,color='red',linestyle='-.',width=0.5),
        mpf.make_addplot(RSI70,ylim=(10, 90),panel=2,color='red',linestyle='-.',width=0.5),
        mpf.make_addplot(data['MACD'],type='bar',width=0.7,panel=3,color=colors),
        mpf.make_addplot(data['MACDs'],panel=3,color='blue',width=0.75),
    ]

    filename = f"./plots/order_{symbol}.png"
    mpf.plot(
        data,
        volume=True,
        figratio=(8, 6),
        panel_ratios=(8,2,2,2),
        type="candle",
        title=f'{symbol} ({config.timeframe} @ {data.index[-1]})',
        addplot=added_plots,
        tight_layout=True,
        style="yahoo",
        savefig=filename,
    )

    notify.Send_Image(f'{symbol}{msg}', image_path=filename)
    # await sleep(2)
    # os.remove(filename)
    return

def add_indicator(symbol, bars):
    df = pd.DataFrame(
        bars, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).map(
        lambda x: x.tz_convert("Asia/Bangkok")
    )
    df = df.set_index("timestamp")

    # เอาข้อมูลใหม่ไปต่อท้าย ข้อมูลที่มีอยู่
    if symbol in all_candles.keys() and len(df) < CANDLE_LIMIT:
        df = pd.concat([all_candles[symbol], df], ignore_index=False)

        # เอาแท่งซ้ำออก เหลืออันใหม่สุด
        df = df[~df.index.duplicated(keep='last')].tail(CANDLE_LIMIT)

    df = df.tail(CANDLE_LIMIT)

    # คำนวนค่าต่างๆใหม่
    df['fast'] = 0
    df['mid'] = 0
    df['slow'] = 0

    try:
        fastType = config.Fast_Type 
        fastValue = config.Fast_Value
        midType = config.Mid_Type 
        midValue = config.Mid_Value        
        slowType = config.Slow_Type 
        slowValue = config.Slow_Value

        if symbol in symbols_setting.index:
            # print(symbols_setting.loc[symbol])
            fastType = symbols_setting.loc[symbol]['fast_type']
            fastValue = int(symbols_setting.loc[symbol]['fast_value'])
            midType = symbols_setting.loc[symbol]['mid_type']
            midValue = int(symbols_setting.loc[symbol]['mid_value'])
            slowType = symbols_setting.loc[symbol]['slow_type']
            slowValue = int(symbols_setting.loc[symbol]['slow_value'])

        if fastType == 'EMA':
            df['fast'] = ta.ema(df['close'],fastValue)
        elif fastType == 'SMA':
            df['fast'] = ta.sma(df['close'],fastValue)
        elif fastType == 'HMA':
            df['fast'] = ta.hma(df['close'],fastValue)
        elif fastType == 'RMA':
            df['fast'] = ta.rma(df['close'],fastValue)
        elif fastType == 'WMA':
            df['fast'] = ta.wma(df['close'],fastValue)
        elif fastType == 'VWMA':
            df['fast'] = ta.vwma(df['close'],df['volume'],fastValue)

        if midType == 'EMA':
            df['mid'] = ta.ema(df['close'],midValue)
        elif midType == 'SMA':
            df['mid'] = ta.sma(df['close'],midValue)
        elif midType == 'HMA':
            df['mid'] = ta.hma(df['close'],midValue)
        elif midType == 'RMA':
            df['mid'] = ta.rma(df['close'],midValue)
        elif midType == 'WMA':
            df['mid'] = ta.wma(df['close'],midValue)
        elif midType == 'VWMA':
            df['mid'] = ta.vwma(df['close'],df['volume'],midValue)

        if slowType == 'EMA':
            df['slow'] = ta.ema(df['close'],slowValue)
        elif slowType == 'SMA':
            df['slow'] = ta.sma(df['close'],slowValue)
        elif slowType == 'HMA':
            df['slow'] = ta.hma(df['close'],slowValue)
        elif slowType == 'RMA':
            df['slow'] = ta.rma(df['close'],slowValue)
        elif slowType == 'WMA':
            df['slow'] = ta.wma(df['close'],slowValue)
        elif slowType == 'VWMA':
            df['slow'] = ta.vwma(df['close'],df['volume'],slowValue)

        # cal MACD
        ewm_fast     = df['close'].ewm(span=config.MACD_FAST, adjust=False).mean()
        ewm_slow     = df['close'].ewm(span=config.MACD_SLOW, adjust=False).mean()
        df['MACD']   = ewm_fast - ewm_slow
        df['MACDs']  = df['MACD'].ewm(span=config.MACD_SIGNAL).mean()
        df['MACDh']  = df['MACD'] - df['MACDs']

        # cal RSI
        # change = df['close'].diff(1)
        # gain = change.mask(change<0,0)
        # loss = change.mask(change>0,0)
        # avg_gain = gain.ewm(com = config.RSI_PERIOD-1,min_periods=config.RSI_PERIOD).mean()
        # avg_loss = loss.ewm(com = config.RSI_PERIOD-1,min_periods=config.RSI_PERIOD).mean()
        # rs = abs(avg_gain / avg_loss)
        # df["RSI"] = 100 - ( 100 / ( 1 + rs ))
        df["RSI"] = ta.rsi(df['close'],config.RSI_PERIOD)

    except Exception as ex:
        print(type(ex).__name__, str(ex))

    return df

"""
fetch_ohlcv - อ่านแท่งเทียน
exchange: binance exchange
symbol: coins symbol
timeframe: candle time frame
limit: จำนวนแท่งที่ต้องการ, ใส่ 0 หากต้องการให้เอาแท่งใหม่ที่ไม่มาครบ
timestamp: ระบุเวลาปัจจุบัน ถ้า limit=0
"""
async def fetch_ohlcv(exchange, symbol, timeframe, limit=1, timestamp=0):
    try:
        # กำหนดการอ่านแท่งเทียนแบบไม่ระบุจำนวน
        if limit == 0 and symbol in all_candles.keys():
            timeframe_secs = TIMEFRAME_SECONDS[timeframe]
            last_candle_time = int(pd.Timestamp(all_candles[symbol].index[-1]).tz_convert('UTC').timestamp())
            # if symbol == "BTCUSDT":
            #     print('----->', timestamp, last_candle_time, timestamp-last_candle_time, (timestamp-last_candle_time)/timeframe_secs)
            # ให้อ่านแท่งสำรองเพิ่มอีก 2 แท่ง
            ohlcv_bars = await exchange.fetch_ohlcv(symbol, timeframe, None, round(2.5+(timestamp-last_candle_time)/timeframe_secs))
            # if symbol == "BTCUSDT":
            #     print('----->', f'จำนวนแท่งใหม่ที่ได้รับ คือ {len(ohlcv_bars)}')
        else:
            ohlcv_bars = await exchange.fetch_ohlcv(symbol, timeframe, None, limit)
        if len(ohlcv_bars):
            all_candles[symbol] = add_indicator(symbol, ohlcv_bars)
            # print(symbol)
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        if limit == 0 and symbol in all_candles.keys():
            print('----->', timestamp, last_candle_time, timestamp-last_candle_time, round(2.5+(timestamp-last_candle_time)/timeframe_secs))

async def set_leverage(exchange, symbol, marginType):
    try:
        if config.automaxLeverage == "on":
            symbol_ccxt = all_symbols[symbol]
            params  = {"settle": marginType}
            lv_tiers = await exchange.fetchLeverageTiers([symbol], params=params)
            leverage = int(lv_tiers[symbol_ccxt][0]['maxLeverage'])
            # print(symbol, symbol_ccxt, leverage)
            await exchange.set_leverage(leverage, symbol)
        else:
            leverage = config.Leverage
            if symbol in symbols_setting.index:
                leverage = int(symbols_setting.loc[symbol]['leverage'])
            await exchange.set_leverage(leverage, symbol)

        # เก็บค่า leverage ไว้ใน all_leverage เพื่อเอาไปใช้ต่อที่อื่น
        all_leverage[symbol] = leverage
    except Exception as ex:
        # print(type(ex).__name__, str(ex))
        leverage = 5
        if type(ex).__name__ == 'ExchangeError' and '-4300' in str(ex):
            leverage = 20
        print(symbol, f'found leverage error, bot will set leverage = {leverage}')

        # เก็บค่า leverage ไว้ใน all_leverage เพื่อเอาไปใช้ต่อที่อื่น
        all_leverage[symbol] = leverage
        try:
            await exchange.set_leverage(leverage, symbol)
        except Exception as ex:
            # print(type(ex).__name__, str(ex))
            print(symbol, f'skip set leverage for {symbol}')

async def fetch_ohlcv_trade(exchange, symbol, timeframe, limit=1, timestamp=0):
    await fetch_ohlcv(exchange, symbol, timeframe, limit, timestamp)
    await gather( go_trade(exchange, symbol) )

# trading zone -----------------------------------------------------------------
async def long_enter(exchange, symbol, amount):
    order = await exchange.create_market_buy_order(symbol, amount)
    # print("Status : LONG ENTERING PROCESSING...")
    logger.info(order)
    return
#-------------------------------------------------------------------------------
async def long_close(exchange, symbol, positionAmt):
    order = await exchange.create_market_sell_order(symbol, positionAmt, params={"reduceOnly":True})
    logger.info(order)
    return
#-------------------------------------------------------------------------------
async def short_enter(exchange, symbol, amount):
    order = await exchange.create_market_sell_order(symbol, amount)
    # print("Status : SHORT ENTERING PROCESSING...")
    logger.info(order)
    return
#-------------------------------------------------------------------------------
async def short_close(exchange, symbol, positionAmt):
    order = await exchange.create_market_buy_order(symbol, (positionAmt*-1), params={"reduceOnly":True})
    logger.info(order)
    return
#-------------------------------------------------------------------------------
async def cancel_order(exchange, symbol):
    await sleep(1)
    order = await exchange.cancel_all_orders(symbol, params={'conditionalOrdersOnly':False})
    logger.info(order)
    return 
#-------------------------------------------------------------------------------
async def long_TPSL(exchange, symbol, amount, PriceEntry, pricetp, pricesl, closeRate):
    closetp=(closeRate/100)
    params = {
        'reduceOnly': True
    }
    params['stopPrice'] = pricetp
    order = await exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'sell', (amount*closetp), PriceEntry, params)
    logger.info(order)
    await sleep(1)
    params['stopPrice'] = pricesl
    order = await exchange.create_order(symbol, 'STOP_MARKET', 'sell', amount, PriceEntry, params)
    logger.info(order)
    await sleep(1)
    return
#-------------------------------------------------------------------------------
async def long_TLSTOP(exchange, symbol, amount, priceTL, callbackRate):
    params = {
        # 'quantityIsRequired': False, 
        'activationPrice': priceTL, 
        'callbackRate': callbackRate, 
        'reduceOnly': True
    }
    order = await exchange.create_order(symbol, 'TRAILING_STOP_MARKET', 'sell', amount, None, params)
    logger.info(order)
    await sleep(1)
    return
#-------------------------------------------------------------------------------
async def short_TPSL(exchange, symbol, amount, PriceEntry, pricetp, pricesl, closeRate):
    closetp=(closeRate/100)
    params = {
        'quantityIsRequired': False, 
        'reduceOnly': True
    }
    params['stopPrice'] = pricetp
    order = await exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'buy', (amount*closetp), PriceEntry, params)
    logger.info(order)
    await sleep(1)
    params['stopPrice'] = pricesl
    order = await exchange.create_order(symbol, 'STOP_MARKET', 'buy', amount, PriceEntry, params)        
    logger.info(order)           
    await sleep(1)
    return
#-------------------------------------------------------------------------------
async def short_TLSTOP(exchange, symbol, amount, priceTL, callbackRate):
    params = {
        'quantityIsRequired': False, 
        'activationPrice': priceTL, 
        'callbackRate': callbackRate, 
        'reduceOnly': True
    }
    order = await exchange.create_order(symbol, 'TRAILING_STOP_MARKET', 'buy', amount, None, params)
    logger.info(order)
    await sleep(1)
    return
#-------------------------------------------------------------------------------
async def cal_amount(exchange, symbol, leverage, costType, costAmount, closePrice, chkLastPrice):
    # คำนวนจำนวนเหรียญที่ใช้เปิดออเดอร์
    priceEntry = float(closePrice)
    # minAmount = float(all_symbols[symbol]['minAmount'])
    # minCost = float(all_symbols[symbol]['minCost'])
    if chkLastPrice:
        try:
            ticker = await exchange.fetch_ticker(symbol)
            priceEntry = float(ticker['last'])
        except Exception as ex:
            print(type(ex).__name__, str(ex))
    if costType=='#':
        amount = costAmount / priceEntry
    elif costType=='$':
        amount = costAmount * float(leverage) / priceEntry
    # elif costType=='M':
    #     # amount = priceEntry * minAmount / float(leverage) * 1.1
    #     amount =  minCost / float(leverage) / priceEntry * 1.1 
    else:
        amount = (float(balance_entry)/100) * costAmount * float(leverage) / priceEntry
    logger.info(f'{symbol} lev:{leverage} close:{closePrice} last:{priceEntry} amt:{amount}')
    return (priceEntry, amount)

async def go_trade(exchange, symbol, chkLastPrice=True):
    global all_positions, balance_entry, count_trade

    # อ่านข้อมูลแท่งเทียนที่เก็บไว้ใน all_candles
    if symbol in all_candles.keys() and len(all_candles[symbol]) >= CANDLE_LIMIT:
        df = all_candles[symbol]
    else:
        print(f'not found candles for {symbol}')
        return
    # อ่านข้อมูล leverage ที่เก็บไว้ใน all_leverage
    if symbol in all_leverage.keys():
        leverage = all_leverage[symbol]
    else:
        print(f'not found leverage for {symbol}')
        return

    limitTrade = config.limit_Trade

    hasLongPosition = False
    hasShortPosition = False
    positionAmt = 0.0
    
    positionInfo = all_positions.loc[all_positions['symbol']==symbol]

    #market_info = pd.DataFrame(await exchange.fapiPrivate_get_positionrisk(), columns=["symbol", "entryPrice", "leverage" ,"unrealizedProfit", "isolatedWallet", "positionAmt"])

    if not positionInfo.empty and positionInfo.iloc[-1]["positionAmt"] != 0:
        positionAmt = float(positionInfo.iloc[-1]["positionAmt"])

    hasLongPosition = (positionAmt > 0)
    hasShortPosition = (positionAmt < 0)

    # print(countTrade, positionAmt, hasLongPosition, hasShortPosition, amount)

    # if positionAmt == 0:
    #     await cancel_order(exchange, symbol)

    try:
        signalIdx = config.SignalIndex
        tradeMode = config.Trade_Mode
        TPSLMode = config.TPSL_Mode
        trailingStopMode = config.Trailing_Stop_Mode
        costType = config.CostType
        costAmount = config.CostAmount
        if symbol in symbols_setting.index:
            signalIdx = int(symbols_setting.loc[symbol]['signal_index'])
            tradeMode = symbols_setting.loc[symbol]['trade_mode']
            TPSLMode = symbols_setting.loc[symbol]['tpsl_mode']
            trailingStopMode = symbols_setting.loc[symbol]['trailing_stop_mode']
            costType = symbols_setting.loc[symbol]['cost_type']
            costAmount = float(symbols_setting.loc[symbol]['cost_amount'])

        fast = (df.iloc[signalIdx-1]['fast'], df.iloc[signalIdx]['fast'])
        mid = (df.iloc[signalIdx-1]['mid'], df.iloc[signalIdx]['mid'])
        slow = (df.iloc[signalIdx-1]['slow'], df.iloc[signalIdx]['slow'])
        # ขึ้น-กระทิง
        isBullish = (fast[0] < slow[0] and fast[1] > slow[1])
        isBullishExit = (fast[0] < mid[0] and fast[1] > mid[1])
        # ลง-หมี
        isBearish = (fast[0] > slow[0] and fast[1] < slow[1])
        isBearishExit = (fast[0] > mid[0] and fast[1] < mid[1])
        # print(symbol, isBullish, isBearish, fast, slow)

        closePrice = df.iloc[-1]["close"]

        if tradeMode == 'on' and isBullishExit == True and hasShortPosition == True:
            count_trade = count_trade-1 if count_trade > 0 else 0
            await short_close(exchange, symbol, positionAmt)
            print(f"[{symbol}] สถานะ : Short Exit processing...")
            notify.Send_Text(f'{symbol}\nสถานะ : Short Exit')
            await cancel_order(exchange, symbol)

        elif tradeMode == 'on' and isBearishExit == True and hasLongPosition == True:
            count_trade = count_trade-1 if count_trade > 0 else 0
            await long_close(exchange, symbol, positionAmt)
            print(f"[{symbol}] สถานะ : Long Exit processing...")
            notify.Send_Text(f'{symbol}\nสถานะ : Long Exit')
            await cancel_order(exchange, symbol)

        notify_msg = []
        notify_msg.append(symbol)

        if isBullish == True and config.Long == 'on' and hasLongPosition == False:
            TPLong = config.TP_Long
            TPCloseLong = config.TPclose_Long
            SLLong = config.SL_Long
            callbackLong = config.Callback_Long
            activeTLLong = config.Active_TL_Long
            if symbol in symbols_setting.index:
                TPLong = float(symbols_setting.loc[symbol]['tp_long'])
                TPCloseLong = float(symbols_setting.loc[symbol]['tp_close_long'])
                SLLong = float(symbols_setting.loc[symbol]['sl_long'])
                callbackLong = float(symbols_setting.loc[symbol]['callback_long'])
                activeTLLong = float(symbols_setting.loc[symbol]['active_tl_long'])

            # print(symbol, 'isBullish')
            # print(symbol, tradeMode, limitTrade, count_trade, balance_entry, config.Not_Trade, priceEntry, amount)
            # print(f'{symbol:12} LONG  {count_trade} {balance_entry:-10.2f} {priceEntry:-10.4f} {amount:-10.4f}')
            print(f'{symbol:12} LONG')
            if tradeMode == 'on' and limitTrade > count_trade and balance_entry > config.Not_Trade:
                (priceEntry, amount) = await cal_amount(exchange, symbol, leverage, costType, costAmount, closePrice, chkLastPrice)
                # ปรับปรุงค่า balance_entry
                balance_entry -= (amount * priceEntry / leverage)
                print('balance_entry', balance_entry)
                count_trade += 1
                await long_enter(exchange, symbol, amount)
                print(f"[{symbol}] Status : LONG ENTERING PROCESSING...")
                await cancel_order(exchange, symbol)
                notify_msg.append('สถานะ : Long\nCross Up')
            
                if TPSLMode =='on':
                    pricetp = priceEntry + (priceEntry * (TPLong / 100.0))
                    pricesl = priceEntry - (priceEntry * (SLLong / 100.0))
                    await long_TPSL(exchange, symbol, amount, priceEntry, pricetp, pricesl, TPCloseLong)
                    print(f'[{symbol}] Set TP {pricetp} SL {pricesl}')
                    notify_msg.append(f'สถานะ : Long set TPSL\nTP: {TPLong}%\nTP close: {TPCloseLong}%\nSL: {SLLong}%')
                if trailingStopMode =='on':
                    priceTL = priceEntry +(priceEntry * (activeTLLong / 100.0))
                    await long_TLSTOP(exchange, symbol, amount, priceTL, callbackLong)
                    print(f'[{symbol}] Set Trailing Stop {priceTL}')
                    notify_msg.append(f'สถานะ : Long set TrailingStop\nCall Back: {callbackLong}%\nActive Price: {round(priceTL,5)} {config.MarginType}')

                gather( line_chart(symbol, df, '\n'.join(notify_msg)) )
                
            elif tradeMode != 'on' :
                gather( line_chart(symbol, df, f'{symbol}\nสถานะ : Long\nCross Up') )

        elif isBearish == True and config.Short == 'on' and hasShortPosition == False:
            TPShort = config.TP_Short
            TPCloseShort = config.TPclose_Short
            SLShort = config.SL_Short
            callbackShort = config.Callback_Short
            activeTLShort = config.Active_TL_Short
            if symbol in symbols_setting.index:
                TPShort = float(symbols_setting.loc[symbol]['tp_short'])
                TPCloseShort = float(symbols_setting.loc[symbol]['tp_close_short'])
                SLShort = float(symbols_setting.loc[symbol]['sl_short'])
                callbackShort = float(symbols_setting.loc[symbol]['callback_short'])
                activeTLShort = float(symbols_setting.loc[symbol]['active_tl_short'])

            # print(symbol, 'isBearish')
            # print(symbol, tradeMode, limitTrade, count_trade, balance_entry, config.Not_Trade, priceEntry, amount)
            # print(f'{symbol:12} SHORT {count_trade} {balance_entry:-10.2f} {priceEntry:-10.4f} {amount:-10.4f}')
            print(f'{symbol:12} SHORT')
            if tradeMode == 'on' and limitTrade > count_trade and balance_entry > config.Not_Trade:
                (priceEntry, amount) = await cal_amount(exchange, symbol, leverage, costType, costAmount, closePrice, chkLastPrice)
                # ปรับปรุงค่า balance_entry
                balance_entry -= (amount * priceEntry / leverage)
                print('balance_entry', balance_entry)
                count_trade += 1
                await short_enter(exchange, symbol, amount)
                print(f"[{symbol}] Status : SHORT ENTERING PROCESSING...")
                await cancel_order(exchange, symbol)
                notify_msg.append('สถานะ : Short\nCross Down')
            
                if TPSLMode == 'on':
                    pricetp = priceEntry - (priceEntry * (TPShort / 100.0))
                    pricesl = priceEntry + (priceEntry * (SLShort / 100.0))
                    await short_TPSL(exchange, symbol, amount, priceEntry, pricetp, pricesl, TPCloseShort)
                    print(f'[{symbol}] Set TP {pricetp} SL {pricesl}')
                    notify_msg.append(f'สถานะ : Short set TPSL\nTP: {TPShort}%\nTP close: {TPCloseShort}%\nSL: {SLShort}%')
                if trailingStopMode == 'on':
                    priceTL = priceEntry - (priceEntry * (activeTLShort / 100.0))
                    await short_TLSTOP(exchange, symbol, amount, priceTL, callbackShort)
                    print(f'[{symbol}] Set Trailing Stop {priceTL}')
                    notify_msg.append(f'สถานะ : Short set TrailingStop\nCall Back: {callbackShort}%\nActive Price: {round(priceTL,5)} {config.MarginType}')
 
                gather( line_chart(symbol, df, '\n'.join(notify_msg)) )

            elif tradeMode != 'on' :
                gather( line_chart(symbol, df, f'{symbol}\nสถานะ : Short\nCross Down') )

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.error(type(ex).__name__, str(ex))
        pass

async def load_all_symbols():
    global all_symbols, watch_list
    try:
        exchange = ccxt.binance({
            "apiKey": config.API_KEY,
            "secret": config.API_SECRET,
            "options": {"defaultType": "future"},
            "enableRateLimit": True}
        )

        # t1=time.time()
        markets = await exchange.fetch_markets()
        # print(markets[0])
        mdf = pd.DataFrame(markets, columns=['id','quote','symbol','limits'])
        mdf.drop(mdf[mdf.quote != config.MarginType].index, inplace=True)
        # mdf.to_csv("fetch_markets.csv",index=False)
        # mdf['minAmount'] = mdf['limits'].apply(lambda x: x['amount']['min'])
        mdf['minCost'] = mdf['limits'].apply(lambda x: x['cost']['min'])
        # print(mdf.columns)
        # print(mdf.head())
        drop_value = ['BTCUSDT_221230','ETHUSDT_221230']
        # all_symbols = {r['id']:{'symbol':r['symbol'],'minAmount':r['minAmount']} for r in mdf[~mdf['id'].isin(drop_value)][['id','symbol','minAmount']].to_dict('records')}
        all_symbols = {r['id']:{'symbol':r['symbol'],'minCost':r['minCost']} for r in mdf[~mdf['id'].isin(drop_value)][['id','symbol','minCost']].to_dict('records')}
        # print(all_symbols, len(all_symbols))
        # print(all_symbols.keys())
        if len(config.watch_list) > 0:
            watch_list_tmp = list(filter(lambda x: x in all_symbols.keys(), config.watch_list))
        else:
            watch_list_tmp = all_symbols.keys()
        # remove sysbol if in back_list
        watch_list = list(filter(lambda x: x not in config.back_list, watch_list_tmp))
        # print(watch_list)
        # t2=(time.time())-t1
        # print(f'ใช้เวลาหาว่ามีเหรียญ เทรดฟิวเจอร์ : {t2:0.2f} วินาที')
        
        print(f'total     : {len(all_symbols.keys())} symbols')
        print(f'target    : {len(watch_list)} symbols')

        logger.info(f'all:{len(all_symbols.keys())} watch:{len(watch_list)}')

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.error(type(ex).__name__, str(ex))

    finally:
        await exchange.close()

async def set_all_leverage():
    try:
        exchange = ccxt.binance({
            "apiKey": config.API_KEY,
            "secret": config.API_SECRET,
            "options": {"defaultType": "future"},
            "enableRateLimit": True}
        )

        # set leverage
        loops = [set_leverage(exchange, symbol, config.MarginType) for symbol in watch_list]
        await gather(*loops)
        # แสดงค่า leverage
        # print(all_leverage)
        print(f'#leverage : {len(all_leverage.keys())} symbols')

        logger.info(f'leverage:{len(all_leverage.keys())}')

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.error(type(ex).__name__, str(ex))

    finally:
        await exchange.close()

async def fetch_first_ohlcv():
    try:
        exchange = ccxt.binance({
            "apiKey": config.API_KEY,
            "secret": config.API_SECRET,
            "options": {"defaultType": "future"},
            "enableRateLimit": True}
        )

        # ครั้งแรกอ่าน 1000 แท่ง -> CANDLE_LIMIT
        limit = CANDLE_LIMIT

        if TIMEFRAME_SECONDS[config.timeframe] >= TIMEFRAME_SECONDS['4h']:
            # อ่านแท่งเทียนแบบ async และ เทรดตามสัญญาน
            loops = [fetch_ohlcv_trade(exchange, symbol, config.timeframe, limit) for symbol in watch_list]
            await gather(*loops)
        else:
            # อ่านแท่งเทียนแบบ async แต่ ยังไม่เทรด
            loops = [fetch_ohlcv(exchange, symbol, config.timeframe, limit) for symbol in watch_list]
            await gather(*loops)

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.error(type(ex).__name__, str(ex))

    finally:
        await exchange.close()

async def fetch_next_ohlcv(next_ticker):
    try:
        exchange = ccxt.binance({
            "apiKey": config.API_KEY,
            "secret": config.API_SECRET,
            "options": {"defaultType": "future"},
            "enableRateLimit": True}
        )

        # กำหนด limit การอ่านแท่งเทียนแบบ 0=ไม่ระบุจำนวน, n=จำนวน n แท่ง
        limit = 0

        # อ่านแท่งเทียนแบบ async และ เทรดตามสัญญาน
        loops = [fetch_ohlcv_trade(exchange, symbol, config.timeframe, limit, next_ticker) for symbol in watch_list]
        await gather(*loops)

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.error(type(ex).__name__, str(ex))

    finally:
        await exchange.close()

async def update_all_balance(marginType):
    global all_positions, balance_entry, count_trade
    try:
        exchange = ccxt.binance({
            "apiKey": config.API_KEY,
            "secret": config.API_SECRET,
            "options": {"defaultType": "future"},
            "enableRateLimit": True}
        )

        balance = await exchange.fetch_balance()
        positions = balance['info']['positions']
        all_positions = pd.DataFrame([position for position in positions if float(position['positionAmt']) != 0],
            # columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide", "initialMargin"])
            columns=["symbol", "entryPrice", "unrealizedProfit", "positionAmt", "initialMargin"])
        count_trade = len(all_positions)
        freeBalance =  await exchange.fetch_free_balance()
        balance_entry = float(freeBalance[marginType])
        profit_loss = balance_entry-start_balance_entry if start_balance_entry > 0 else 0
        all_positions['unrealizedProfit'] = all_positions['unrealizedProfit'].apply(lambda x: '{:,.2f}'.format(float(x)))
        all_positions['initialMargin'] = all_positions['initialMargin'].apply(lambda x: '{:,.2f}'.format(float(x)))
        all_positions["pd."] = all_positions['positionAmt'].apply(lambda x: 'LONG' if float(x) >= 0 else 'SHORT')
        if config.Trade_Mode == 'on':
            # print("all_positions ================")
            print(all_positions)
            print("countTrade ===================", f'{count_trade}/{config.limit_Trade}')
            print("balance_entry ================", balance_entry, "change", "{:+g}".format(profit_loss))

        logger.info(f'countTrade:{count_trade} balance_entry:{balance_entry}')

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.error(type(ex).__name__, str(ex))

    finally:
        await exchange.close()

async def load_symbols_setting():
    global symbols_setting
    try:
        if config.CSV_NAME:
            symbols_setting = pd.read_csv(config.CSV_NAME, skipinitialspace=True)
            if any(x in CSV_COLUMNS for x in symbols_setting.columns.to_list()):
                symbols_setting.drop(symbols_setting[symbols_setting.margin_type != config.MarginType].index, inplace=True)
                symbols_setting['id'] = symbols_setting['symbol']+symbols_setting['margin_type']
                symbols_setting.set_index('id', inplace=True)
                # เอาอันซ้ำออก เหลืออันใหม่สุด
                symbols_setting = symbols_setting[~symbols_setting.index.duplicated(keep='last')]

                # validate all values
                int_columns = [
                        'fast_value', 'mid_value', 'slow_value', 'signal_index', 'leverage'
                        ]
                float_columns = [
                        'cost_amount', 
                        'tp_long', 'tp_close_long', 'sl_long', 'callback_long', 'active_tl_long',
                        'tp_short', 'tp_close_short', 'sl_short', 'callback_short', 'active_tl_short'
                        ]
                symbols_setting[int_columns] = symbols_setting[int_columns].apply(pd.to_numeric, errors='coerce')
                symbols_setting[float_columns] = symbols_setting[float_columns].apply(pd.to_numeric, downcast='float', errors='coerce')
                symbols_setting.dropna(inplace=True)

                # print(symbols_setting.head())
                # print(symbols_setting.iloc[1])
                # validate all setting

                logger.info(f'success load symbols_setting from {config.CSV_NAME}')
            else:
                symbols_setting = pd.DataFrame(columns=CSV_COLUMNS)
                print(f'fail load symbols_setting from {config.CSV_NAME}, all columns not match')
                logger.info(f'fail load symbols_setting from {config.CSV_NAME}, all columns not match')

    except Exception as ex:
        symbols_setting = pd.DataFrame(columns=CSV_COLUMNS)
        print(type(ex).__name__, str(ex))
        logger.error(type(ex).__name__, str(ex))

async def main():
    global start_balance_entry

    # set cursor At top, left (1,1)
    print(CLS_SCREEN+bot_name)

    # แสดง status waiting ระหว่างที่รอ...
    gather(waiting())

    await load_all_symbols()

    await set_all_leverage()

    await load_symbols_setting()

    # kwargs = dict(
    #     limitTrade=config.limit_Trade,
    # )

    time_wait = TIMEFRAME_SECONDS[config.timeframe] # กำหนดเวลาต่อ 1 รอบ
    time_wait_1m = TIMEFRAME_SECONDS['1m'] # กำหนดเวลา update balance ทุก 1m

    # อ่านแท่งเทียนทุกเหรียญ
    t1=time.time()
    local_time = time.ctime(t1)
    print(f'get all candles: {local_time}')

    await fetch_first_ohlcv()
        
    t2=(time.time())-t1
    print(f'total time : {t2:0.2f} secs')
    logger.info(f'first ohlcv: {t2:0.2f} secs')

    # แสดงค่า positions & balance
    await update_all_balance(config.MarginType)
    start_balance_entry = balance_entry

    try:
        start_ticker = time.time()
        next_ticker = start_ticker - (start_ticker % time_wait) # ตั้งรอบเวลา
        next_ticker += time_wait # กำหนดรอบเวลาถัดไป
        next_ticker_1m = start_ticker - (start_ticker % time_wait_1m)
        next_ticker_1m += time_wait_1m
        while True:
            seconds = time.time()
            if seconds >= next_ticker + TIME_SHIFT: # ครบรอบ
                # set cursor At top, left (1,1)
                print(CLS_SCREEN+bot_name)

                local_time = time.ctime(seconds)
                print(f'calculate new indicator: {local_time}')
                
                await update_all_balance(config.MarginType)

                t1=time.time()

                await fetch_next_ohlcv(next_ticker)

                t2=(time.time())-t1
                print(f'total time : {t2:0.2f} secs')
                logger.info(f'update ohlcv: {t2:0.2f} secs (include trade)')

                next_ticker += time_wait # กำหนดรอบเวลาถัดไป
                next_ticker_1m += time_wait_1m

                await sleep(10)

            elif config.Trade_Mode == 'on' and seconds >= next_ticker_1m + TIME_SHIFT:
                # set cursor At top, left (1,1)
                print(CLS_SCREEN+bot_name)
                balance_time = time.ctime(seconds)
                print(f'last indicator: {local_time}, last balance: {balance_time}')
                await update_all_balance(config.MarginType)
                next_ticker_1m += time_wait_1m

            await sleep(1)

    except KeyboardInterrupt:
        pass

    except Exception as ex:
        print(type(ex).__name__, str(ex))

async def waiting():
    count = 0
    status = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    while True:
        await sleep(1)
        print('\r'+CGREEN+CBOLD+status[count%len(status)]+' waiting...\r'+CEND, end='')
        count += 1
        count = count%len(status)

if __name__ == "__main__":
    try:
        logger.info('start ==========')
        pathlib.Path('./plots').mkdir(parents=True, exist_ok=True) 
        os.system("color") # enables ansi escape characters in terminal
        print(HIDE_CURSOR, end="")
        loop = get_event_loop()
        loop.run_until_complete(main())

    except KeyboardInterrupt:
        print(CLS_LINE+'\rbye')

    except Exception as ex:
        print(type(ex).__name__, str(ex))

    finally:
        print(SHOW_CURSOR, end="")