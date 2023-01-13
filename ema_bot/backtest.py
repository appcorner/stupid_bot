from asyncio import get_event_loop, gather, sleep
import pandas as pd
import pandas_ta as ta
import config

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG

import ccxt.async_support as ccxt

TIME_SHIFT = config.TIME_SHIFT

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

CANDLE_LIMIT = config.CANDLE_LIMIT
CANDLE_PLOT = config.CANDLE_PLOT

all_candles = {}

async def fetch_ohlcv(exchange, symbol, timeframe, limit=1, timestamp=0):
    try:
        # กำหนดการอ่านแท่งเทียนแบบไม่ระบุจำนวน
        if limit == 0 and symbol in all_candles.keys():
            timeframe_secs = TIMEFRAME_SECONDS[timeframe]
            last_candle_time = int(pd.Timestamp(all_candles[symbol].index[-1]).tz_convert('UTC').timestamp())
            # ให้อ่านแท่งสำรองเพิ่มอีก 2 แท่ง
            ohlcv_bars = await exchange.fetch_ohlcv(symbol, timeframe, None, round(1.5+(timestamp-last_candle_time)/timeframe_secs))
        else:
            ohlcv_bars = await exchange.fetch_ohlcv(symbol, timeframe, None, limit)
        if len(ohlcv_bars):
            all_candles[symbol] = add_indicator(symbol, ohlcv_bars)
            # print(symbol)
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        if limit == 0 and symbol in all_candles.keys():
            print('----->', timestamp, last_candle_time, timestamp-last_candle_time, round(2.5+(timestamp-last_candle_time)/timeframe_secs))

def add_indicator(symbol, bars):
    df = pd.DataFrame(
        bars, columns=["timestamp", "Open", "High", "Low", "Close", "Volume"]
    )
    # fake timestamp
    df["timestamp_original"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).map(
        lambda x: x.tz_convert("Asia/Bangkok")
    )
    first_date = date
    df["timestamp"] = 
    df = df.set_index("timestamp")

    # เอาข้อมูลใหม่ไปต่อท้าย ข้อมูลที่มีอยู่
    # if symbol in all_candles.keys() and len(df) < CANDLE_LIMIT:
    #     df = pd.concat([all_candles[symbol], df], ignore_index=False)

    #     # เอาแท่งซ้ำออก เหลืออันใหม่สุด
    #     df = df[~df.index.duplicated(keep='last')].tail(CANDLE_LIMIT)

    df = df.tail(CANDLE_LIMIT)

    print(df.tail(10))

    return df

async def fetch_first_ohlcv(symbol):
    try:
        exchange = ccxt.binance({
            "apiKey": config.API_KEY,
            "secret": config.API_SECRET,
            "options": {"defaultType": "future"},
            "enableRateLimit": True}
        )

        # ครั้งแรกอ่าน 1000 แท่ง -> CANDLE_LIMIT
        limit = CANDLE_LIMIT
        await fetch_ohlcv(exchange, symbol, config.timeframe, limit)

    except Exception as ex:
        print(type(ex).__name__, str(ex))

    finally:
        await exchange.close()


def SMA(arr: pd.Series, n: int) -> pd.Series:
    """
    Returns `n`-period simple moving average of array `arr`.
    """
    return pd.Series(arr).rolling(n).mean()

class EmaCross(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        close = self.data.Close
        self.sma1 = self.I(SMA, close, self.n1)
        self.sma2 = self.I(SMA, close, self.n2)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()

async def main():
    symbol = 'DOGEUSDT'
    await fetch_first_ohlcv(symbol)
    df = all_candles[symbol]
    bt = Backtest(df, EmaCross,
              cash=10000, commission=.08,
              exclusive_orders=True)

    output = bt.run()
    bt.plot()

if __name__ == "__main__":
    try:
        loop = get_event_loop()
        loop.run_until_complete(main())        

    # except KeyboardInterrupt:


    except Exception as ex:
        print(type(ex).__name__, str(ex))

    # finally:
