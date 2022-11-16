from asyncio import get_event_loop, gather, sleep
import pandas as pd
import pandas_ta as ta
import time
from LineNotify import LineNotify
import config

# -----------------------------------------------------------------------------
# API_KEY, API_SECRET, LINE_NOTIFY_TOKEN in config.ini
# -----------------------------------------------------------------------------

import ccxt.async_support as ccxt

# print('CCXT Version:', ccxt.__version__)
# -----------------------------------------------------------------------------

# กำหนดเวลาที่ต้องการเลื่อนการอ่านข้อมูล เป็นจำนวนวินาที
TIME_SHIFT = 5

TIMEFRAME_SECONDS = {
    '1m': 60,
    '5m': 60*5,
    '15m': 60*15,
    '1h': 60*60,
    '4h': 60*60*4,
    '1d': 60*60*24,
}

CANDLE_LIMIT = 1000

# ----------------------------------------------------------------------------
# global variable
# ----------------------------------------------------------------------------
notify = LineNotify(config.LINE_NOTIFY_TOKEN)

all_positions = pd.DataFrame(columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide", "initialMargin"])

balance_entry = 0.0

all_leverage = {}
all_candles = {}


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
    df['slow'] = 0

    try:

        if config.Fast_Type == 'EMA':
            df['fast'] = ta.ema(df['close'],config.Fast_Value)
        elif config.Fast_Type == 'SMA':
            df['fast'] = ta.sma(df['close'],config.Fast_Value)
        elif config.Fast_Type == 'HMA':
            df['fast'] = ta.hma(df['close'],config.Fast_Value)
        elif config.Fast_Type == 'RMA':
            df['fast'] = ta.rma(df['close'],config.Fast_Value)
        elif config.Fast_Type == 'WMA':
            df['fast'] = ta.wma(df['close'],config.Fast_Value)
        elif config.Fast_Type == 'VWMA':
            df['fast'] = ta.vwma(df['close'],df['volume'],config.Fast_Value)

        if config.Slow_Type == 'EMA':
            df['slow'] = ta.ema(df['close'],config.Slow_Value)
        elif config.Slow_Type == 'SMA':
            df['slow'] = ta.sma(df['close'],config.Slow_Value)
        elif config.Slow_Type == 'HMA':
            df['slow'] = ta.hma(df['close'],config.Slow_Value)
        elif config.Slow_Type == 'RMA':
            df['slow'] = ta.rma(df['close'],config.Slow_Value)
        elif config.Slow_Type == 'WMA':
            df['slow'] = ta.wma(df['close'],config.Slow_Value)
        elif config.Slow_Type == 'VWMA':
            df['slow'] = ta.vwma(df['close'],df['volume'],config.Slow_Value)

    except Exception as e:
        print(e)

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
            ohlcv_bars = await exchange.fetch_ohlcv(symbol, timeframe, None, round(0.5+(timestamp-last_candle_time)/timeframe_secs))
            # if symbol == "BTCUSDT":
            #     print('----->', f'จำนวนแท่งใหม่ที่ได้รับ คือ {len(ohlcv_bars)}')
        else:
            ohlcv_bars = await exchange.fetch_ohlcv(symbol, timeframe, None, limit)
        if len(ohlcv_bars):
            all_candles[symbol] = add_indicator(symbol, ohlcv_bars)
            # print(symbol)
    except Exception as e:
        print('----->', timestamp, last_candle_time, timestamp-last_candle_time, round(0.5+(timestamp-last_candle_time)/timeframe_secs))
        print(type(e).__name__, str(e))

async def set_leverage(exchange, symbol):
    try:
        if config.automaxLeverage == "on":
            market_lv = pd.DataFrame(await exchange.fetchMarketLeverageTiers(symbol), columns=["maxLeverage"])
            leverage = int(market_lv["maxLeverage"][0])
            await exchange.set_leverage(leverage, symbol)
        else:
            leverage = config.Leverage
            await exchange.set_leverage(leverage, symbol)

        # เก็บค่า df ไว้ใน object all_leverage เพื่อเอาไปใช้ต่อที่อื่น
        all_leverage[symbol] = leverage
    except Exception as e:
        # print(type(e).__name__, str(e))
        print(symbol, 'Found leverage error bot will Set leverage = 5')
        leverage = 5
        # เก็บค่า df ไว้ใน object all_leverage เพื่อเอาไปใช้ต่อที่อื่น
        all_leverage[symbol] = leverage
        try:
            await exchange.set_leverage(leverage, symbol)
        except Exception as e:
            # print(type(e).__name__, str(e))
            print(symbol, f'skip set leverage for {symbol}')

async def fetch_ohlcv_trade(exchange, symbol, timeframe, limit=1, timestamp=0, **kwargs):
    await fetch_ohlcv(exchange, symbol, timeframe, limit, timestamp)
    await gather(go_trade(exchange, symbol, kwargs['limitTrade']))

async def update_all_balance(exchange, marginType):
    global all_positions, balance_entry

    balance = await exchange.fetch_balance()
    positions = balance['info']['positions']
    all_positions = pd.DataFrame([position for position in positions if float(position['positionAmt']) != 0],
        columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide", "initialMargin"])
    print("all_positions ====================")
    print(all_positions)

    freeBalance =  await exchange.fetch_free_balance()
    balance_entry = float(freeBalance[marginType])
    print("balance_entry ====================")
    print(balance_entry)

# trading zone -----------------------------------------------------------------
async def long_enter(exchange, symbol, amount):
    order = await exchange.create_market_buy_order(symbol, amount)
    # print("Status : LONG ENTERING PROCESSING...")
    return
#-------------------------------------------------------------------------------
async def long_close(exchange, symbol, positionAmt):
    order = await exchange.create_market_sell_order(symbol, positionAmt, params={"reduceOnly":True})
    return
#-------------------------------------------------------------------------------
async def short_enter(exchange, symbol, amount):
    order = await exchange.create_market_sell_order(symbol, amount)
    # print("Status : SHORT ENTERING PROCESSING...")
    return
#-------------------------------------------------------------------------------
async def short_close(exchange, symbol, positionAmt):
    order = await exchange.create_market_buy_order(symbol, (positionAmt*-1), params={"reduceOnly":True})
    return
#-------------------------------------------------------------------------------
async def cancel_order(exchange, symbol):
    order = await exchange.cancel_all_orders(symbol, params={'conditionalOrdersOnly':False})
    return 
#-------------------------------------------------------------------------------
async def long_TPSL(exchange, symbol, amount, PriceEntry, pricetp, pricesl):
    closetp=(config.TPclose/100)
    params = {
        'reduceOnly': True
    }
    params['stopPrice'] = pricetp
    order = await exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'sell', (amount*closetp), PriceEntry, params)
    time.sleep(1)
    params['stopPrice'] = pricesl
    order = await exchange.create_order(symbol, 'STOP_MARKET', 'sell', amount, PriceEntry, params)
    time.sleep(1)
    return
#-------------------------------------------------------------------------------
async def long_TLSTOP(exchange, symbol, amount, PriceEntry, pricetpTL):
    params = {
        # 'quantityIsRequired': False, 
        'activationPrice': pricetpTL, 
        'callbackRate': config.Callback, 
        'reduceOnly': True
    }
    order = await exchange.create_order(symbol, 'TRAILING_STOP_MARKET', 'sell', amount, None, params)
    time.sleep(1)
    return
#-------------------------------------------------------------------------------
async def short_TPSL(exchange, symbol, amount, PriceEntry, pricetp, pricesl):
    closetp=(config.TPclose/100)
    params = {
        'quantityIsRequired': False, 
        'reduceOnly': True
    }
    params['stopPrice'] = pricetp
    order = await exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'buy', (amount*closetp), PriceEntry, params)
    time.sleep(1)
    params['stopPrice'] = pricesl
    order = await exchange.create_order(symbol, 'STOP_MARKET', 'buy', amount, PriceEntry, params)                   
    time.sleep(1)
    return
#-------------------------------------------------------------------------------
async def short_TLSTOP(exchange, symbol, amount, PriceEntry, pricetpTL):
    params = {
        'quantityIsRequired': False, 
        'activationPrice': pricetpTL, 
        'callbackRate': config.Callback, 
        'reduceOnly': True
    }
    order = await exchange.create_order(symbol, 'TRAILING_STOP_MARKET', 'buy', amount, None, params)
    time.sleep(1)
    return
#-------------------------------------------------------------------------------
async def go_trade(exchange, symbol, limitTrade):
    global all_positions, balance_entry

    # อ่านข้อมูลแท่งเทียนที่เก็บไว้ใน all_candles
    if symbol in all_candles.keys() and len(all_candles[symbol]) >= CANDLE_LIMIT:
        df = all_candles[symbol]
    else:
        print(f'ไม่พบข้อมูลแท่งเทียนของ {symbol}')
        return
    # อ่านข้อมูล leverage ที่เก็บไว้ใน all_leverage
    if symbol in all_leverage.keys():
        leverage = all_leverage[symbol]
    else:
        # set default 5 if symbol is not found
        leverage = 5
        return

    hasLongPosition = False
    hasShortPosition = False
    positionAmt = 0.0
    
    countTrade = len(all_positions)
    # currentPositions = [position for position in all_positions if position['symbol'] == symbol]
    
    # positionInfo = pd.DataFrame(currentPositions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide", "initialMargin"])
    positionInfo = all_positions.loc[all_positions['symbol']==symbol]
    if symbol == 'BTCUSDT':
        print("countTrade ====================")
        print(countTrade)
        print("positionInfo ====================")
        print(positionInfo)

    #market_info = pd.DataFrame(await exchange.fapiPrivate_get_positionrisk(), columns=["symbol", "entryPrice", "leverage" ,"unrealizedProfit", "isolatedWallet", "positionAmt"])

    # คำนวนจำนวนเหรียญที่ใช้เปิดออเดอร์
    priceEntry = float(df.iloc[-1]["close"])
    if config.CostType=='#':
        amount = config.CostAmount / priceEntry
    elif config.CostType=='$':
        amount = config.CostAmount * float(leverage) / priceEntry
    else:
        amount = (float(balance_entry)/100) * config.CostAmount * float(leverage) / priceEntry

    if not positionInfo.empty and positionInfo.iloc[-1]["positionAmt"] != 0:
        positionAmt = float(positionInfo.iloc[-1]["positionAmt"])

    hasLongPosition = (positionAmt > 0)
    hasShortPosition = (positionAmt < 0)

    # print(countTrade, positionAmt, hasLongPosition, hasShortPosition, amount)

    # if positionAmt == 0:
    #     await cancelorder(exchange,symbol)

    try:
        signalIdx = -1
        fast = (df.iloc[signalIdx-1]['fast'], df.iloc[signalIdx]['fast'])
        slow = (df.iloc[signalIdx-1]['slow'], df.iloc[signalIdx]['slow'])
        # ขึ้น-กระทิง
        isBullish = (fast[0] < slow[0] and fast[1] > slow[1])
        # ลง-หมี
        isBearish = (fast[0] > slow[0] and fast[1] < slow[1])
        # print(symbol, isBullish, isBearish, fast, slow)
        # if symbol == "BTCUSDT":
        #     print('=================');
        #     for si in range(-3,0):
        #         si_fast = df.iloc[si]['fast']
        #         si_slow = df.iloc[si]['slow']
        #         print(f'[{si}] Fast : {si_fast:0.5f}  Slow : {si_slow:0.5f}')
        #     print('=================');
        #     if isBullish:
        #         print('# Bullish Crossover -> LONG')
        #     elif isBearish:
        #         print('# Bearish Crossover -> SHORT')
        #     else:
        #         print('no signal')

        if isBullish == True:
            # print(symbol, 'isBullish')
            if hasShortPosition == True:
                await short_close(symbol, positionAmt)
                print(f"[{symbol}] สถานะ : Short Exit processing...")
                notify.Send_Text(f'{symbol}\n สถานะ : Short Exit')
                await cancel_order(exchange, symbol)
            elif config.Long == 'on' and hasLongPosition == False:
                print(symbol, config.Trade_Mode, limitTrade, countTrade, balance_entry, config.Not_Trade, priceEntry, amount)
                if config.Trade_Mode == 'on' and limitTrade >= countTrade and balance_entry > config.Not_Trade:
                    # ปรับปรุงค่า balance_entry
                    balance_entry -= (amount * priceEntry / leverage)
                    print('balance_entry', balance_entry)
                    await long_enter(exchange, symbol, amount)
                    print(f"[{symbol}] Status : LONG ENTERING PROCESSING...")
                    await cancel_order(exchange, symbol)
                    notify.Send_Text(f'{symbol}\n สถานะ : Long\nCross Up')
                
                    if config.TPSL_Mode =='on':
                        pricetp = priceEntry + (priceEntry * (config.TP / 100.0))
                        pricesl = priceEntry - (priceEntry * (config.SL / 100.0))
                        await long_TPSL(exchange, symbol, amount, priceEntry, pricetp, pricesl)
                        print(f'[{symbol}] Set TP {pricetp} SL {pricesl}')
                        notify.Send_Text(f'{symbol}\n สถานะ : Long set TPSL\nTP: {config.TP}%\nTP close: {config.TPclose}%\nSL: {config.SL}%')
                    if config.Trailing_Stop_Mode =='on':
                        pricetpTL = priceEntry +(priceEntry * (config.Active_TL / 100.0))
                        await long_TLSTOP(exchange, symbol, amount, priceEntry, pricetpTL)
                        print(f'[{symbol}] Set Trailing Stop {pricetpTL}')
                        notify.Send_Text(f'{symbol}\n สถานะ : Long set TrailingStop\nCall Back: {config.Callback}%\nActive Price: {round(pricetpTL,5)} {config.MarginType}')
                # else:
                #     notify.Send_Text('Canot trade will sent alert only')
                # Line(symbol,df)

        elif isBearish == True:
            # print(symbol, 'isBearish')
            if hasLongPosition == True:
                await long_close(symbol, positionAmt)
                print(f"[{symbol}] สถานะ : Long Exit processing...")
                notify.Send_Text(f'{symbol}\n สถานะ : Long Exit')
                await cancel_order(exchange, symbol)
            elif config.Short == 'on' and hasShortPosition == False:
                print(symbol, config.Trade_Mode, limitTrade, countTrade, balance_entry, config.Not_Trade, priceEntry, amount)
                if config.Trade_Mode == 'on' and limitTrade >= countTrade and balance_entry > config.Not_Trade:
                    # ปรับปรุงค่า balance_entry
                    balance_entry -= (amount * priceEntry / leverage)
                    print('balance_entry', balance_entry)
                    await short_enter(exchange, symbol, amount)
                    print(f"[{symbol}] Status : SHORT ENTERING PROCESSING...")
                    await cancel_order(exchange, symbol)
                    notify.Send_Text(f'{symbol}\n สถานะ : Short\nCross Down')
                
                    if config.TPSL_Mode == 'on':
                        pricetp = priceEntry - (priceEntry * (float(config.TP) / 100.0))
                        pricesl = priceEntry + (priceEntry * (float(config.SL) / 100.0))
                        await short_TPSL(exchange, symbol, amount, priceEntry, pricetp, pricesl)
                        print(f'[{symbol}] Set TP {pricetp} SL {pricesl}')
                        notify.Send_Text(f'{symbol}\n สถานะ : Short set TPSL\nTP: {config.TP}%\nTP close: {config.TPclose}%\nSL: {config.SL}%')
                    if config.Trailing_Stop_Mode == 'on':
                        pricetpTL = priceEntry - (priceEntry * (float(config.Active_TL) / 100.0))
                        await short_TLSTOP(exchange, symbol, amount, priceEntry, pricetpTL)
                        print(f'[{symbol}] Set Trailing Stop {pricetpTL}')
                        notify.Send_Text(f'{symbol}\n สถานะ : Short set TrailingStop\nCall Back: {config.Callback}%\nActive Price: {round(pricetpTL,5)} {config.MarginType}')
                # else:
                #     notify.Send_Text('Canot trade will sent alert only')
                # Line(symbol,df)

    except Exception as e:
        print(type(e).__name__, str(e))
        pass

async def main():
    # global all_candles
    exchange = ccxt.binance({
        "apiKey": config.API_KEY,
        "secret": config.API_SECRET,
        "options": {"defaultType": "future"},
        "enableRateLimit": True}
    )
    t1=time.time()
    markets = await exchange.fetch_markets()
    # print(markets[0])
    mdf = pd.DataFrame(markets, columns=['id','quote'])
    mdf.drop(mdf[mdf.quote != 'USDT'].index, inplace=True)
    # print(mdf.columns)
    # print(mdf.head())
    drop_value = ['BTCUSDT_221230','ETHUSDT_221230']
    symbols = mdf[~mdf['id'].isin(drop_value)]['id'].to_list()
    # print(symbols)
    t2=(time.time())-t1
    print(f'ใช้เวลาหาว่ามีเหรียญ เทรดฟิวเจอร์ : {t2:0.2f} วินาที')
    print(f'จำนวนเหรียญ : {len(symbols)} เหรียญ')

    kwargs = dict(
        limitTrade=config.limit_Trade,
    )

    # set leverage
    # print(all_leverage)
    loops = [set_leverage(exchange, symbol) for symbol in symbols]
    await gather(*loops)
    # แสดงค่า leverage
    # print(all_leverage)
    print(f'จำนวนค่า leverage ที่คำนวนได้ {len(all_leverage.keys())}')

    time_wait = TIMEFRAME_SECONDS[config.timeframe] # กำหนดเวลาต่อ 1 รอบ
    # ครั้งแรกอ่าน 1000 แท่ง -> CANDLE_LIMIT
    limit = CANDLE_LIMIT

    # await update_all_balance(exchange, config.MarginType)

    # อ่านแท่งเทียนย้อนหลัง
    t1=time.time()
    local_time = time.ctime(t1)
    print(f'เริ่มอ่านแท่งเทียนย้อนหลัง ที่ {local_time}')

    # อ่านแท่งเทียนแบบ async 
    loops = [fetch_ohlcv(exchange, symbol, config.timeframe, limit) for symbol in symbols]
    await gather(*loops)
    # อ่านแท่งเทียนแบบ async และ เทรดตามสัญญาน
    # loops = [fetch_ohlcv_trade(exchange, symbol, timeframe, limit, **kwargs) for symbol in symbols]
    # await gather(*loops)
    
    t2=(time.time())-t1
    print(f'อ่านแท่งเทียนทุกเหรียญใช้เวลา : {t2:0.2f} วินาที')

    # ตรวจสอบว่าได้ข้อมูลครบจริงไหม
    # print(f'--> ได้รับข้อมูลแท่งเทียน จำนวน {len(all_candles.keys())} เหรียญ')
    # แสดงข้อมูลตัวอย่างของ BTCUSDT
    # print(all_candles['BTCUSDT'].head(3))
    # print(all_candles['BTCUSDT'].tail(5))
    
    count = 0
    SHOW_CURSOR = '\033[?25h'
    HIDE_CURSOR = '\033[?25l'
    CGREEN  = '\33[32m'
    CEND = '\033[0m'
    CBOLD = '\33[1m'
    status = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    try:
        print(HIDE_CURSOR, end="")

        next_ticker = time.time()
        next_ticker -= (next_ticker % time_wait) # ตั้งรอบเวลา
        next_ticker += time_wait # กำหนดรอบเวลาถัดไป
        while True:
            seconds = time.time()
            if seconds >= next_ticker + TIME_SHIFT: # ครบรอบ
                local_time = time.ctime(seconds)
                print(f'\rเริ่มเช็คค่าอินดิเคเตอร์ ที่ {local_time}')
                
                await update_all_balance(exchange, config.MarginType)

                t1=time.time()

                # กำหนดการอ่านแท่งเทียนแบบ 0=ไม่ระบุจำนวน, n=จำนวน n แท่ง
                limit = 0
                # อ่านแท่งเทียนแบบ async 
                # loops = [fetch_ohlcv(exchange, symbol, timeframe, limit, next_ticker) for symbol in symbols]
                # await gather(*loops)
                # อ่านแท่งเทียนแบบ async และ เทรดตามสัญญาน
                loops = [fetch_ohlcv_trade(exchange, symbol, config.timeframe, limit, next_ticker, **kwargs) for symbol in symbols]
                await gather(*loops)

                next_ticker += time_wait # กำหนดรอบเวลาถัดไป

                t2=(time.time())-t1
                print(f'ตรวจสอบอินดิเคเตอร์ทุกเหรียญใช้เวลา : {t2:0.2f} วินาที')

                # ตรวจสอบว่าได้ข้อมูลครบจริงไหม
                # print(f'--> ได้รับข้อมูลแท่งเทียน จำนวน {len(all_candles.keys())} เหรียญ')
                # แสดงข้อมูลตัวอย่างของ BTCUSDT
                # print(all_candles['BTCUSDT'].head(3))
                # print(all_candles['BTCUSDT'].tail(8))
                # print(f"จำนวนแท่ง: {len(all_candles['BTCUSDT'])}")

                # trade all symbols
                # t1=time.time()

                # loops = [go_trade(exchange, symbol, limit_Trade, balanceposition, BalanceEntry) for symbol in symbols]
                # await gather(*loops)

                # t2=(time.time())-t1
                # print(f'Total time trade : {t2:0.2f} seconds')

                break

            await sleep(1)
            print('\r'+CGREEN+CBOLD+status[count%len(status)]+' waiting...'+CEND, end='')
            count += 1
            count = count%len(status)

    except KeyboardInterrupt:
        print('exit')

    finally:
        await exchange.close()
        print(SHOW_CURSOR, end="")

if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())