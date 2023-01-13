from asyncio import get_event_loop, gather, sleep
import pandas as pd
import ccxt.async_support as ccxt
import time

API_KEY = ""
API_SECRET = ""

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

TIME_SHIFT = 5

async def fetch_ohlcv(exchange, symbol):
    ohlc = await exchange.fetch_ohlcv(symbol, '1d', None, 2)
    ohlc[0].insert(0, symbol)
    return ohlc[0]

async def fetch_tickers(exchange, symbols):
    tickers = await exchange.fetch_tickers()
    # print(tickers)
    tickers_ohlc = [[
        symbol,
        tickers[symbol]['timestamp'],
        tickers[symbol]['open'],
        tickers[symbol]['high'],
        tickers[symbol]['low'],
        tickers[symbol]['close'],
        tickers[symbol]['baseVolume'],
        ] for symbol in symbols]
    return tickers_ohlc

async def read_1d_ohlc(ex, spot_symbols):

    start_tm = time.time()
    local_time = time.ctime(start_tm)
    print(f'start ohlc: {local_time}')

    # Create a list of tasks to fetch the OHLCV data for each symbol
    tasks = [fetch_ohlcv(ex, symbol) for symbol in spot_symbols]

    # Wait for all tasks to complete
    data = await gather(*tasks)

    # print(data)
    df = pd.DataFrame(data, columns=['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Calculate the percent change for each symbol
    df['percent_change'] = (df['close'] - df['open']) / df['open']

    # Print the results
    # print(df.head(2))
    print(df.tail(3))

    diff=(time.time())-start_tm
    print(f'ohlc time: {diff:0.2f} secs')

async def read_tf_ticker(ex, spot_symbols):

    start_tm = time.time()
    local_time = time.ctime(start_tm)
    print(f'start ticker: {local_time}')

    tickers_data = await fetch_tickers(ex, spot_symbols)

    tk_df = pd.DataFrame(tickers_data, columns=['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Calculate the percent change for each symbol
    tk_df['percent_change'] = (tk_df['close'] - tk_df['open']) / tk_df['open']

    # print(tk_df.head(2))
    print(tk_df.tail(3))

    diff=(time.time())-start_tm
    print(f'ticker time: {diff:0.2f} secs')

async def main():
    ex = ccxt.binance({
        "apiKey": API_KEY,
        "secret": API_SECRET,
        "options": {"defaultType": "spot"},
        "enableRateLimit": True}
    )
    symbols = await ex.fetch_markets()
    spot_symbols = [symbol['symbol'] for symbol in symbols if symbol['type'] == 'spot' and symbol['quote'] == 'USDT']
    # print(spot_symbols)
    
    # ListTopChange = []

    time_wait_1d = TIMEFRAME_SECONDS['1d'] # กำหนดเวลาต่อ 1 days
    time_wait_tf = TIMEFRAME_SECONDS['3m'] # กำหนดเวลาต่อ 1 รอบ

    await read_1d_ohlc(ex, spot_symbols)

    try:
        count = 0
        status = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

        start_ticker = time.time()
        next_ticker_1d = start_ticker - (start_ticker % time_wait_1d)
        next_ticker_1d += time_wait_1d # กำหนดรอบเวลา 1 วันถัดไป
        next_ticker_tf = start_ticker - (start_ticker % time_wait_tf)
        next_ticker_tf += time_wait_tf # กำหนดรอบเวลาถัดไป
        while True:
            seconds = time.time()

            if seconds >= next_ticker_1d + TIME_SHIFT: # ครบรอบ 1d
                
                await read_1d_ohlc(ex, spot_symbols)

                next_ticker_1d += time_wait_1d # กำหนดรอบเวลาถัดไป

            if seconds >= next_ticker_tf + TIME_SHIFT: # ครบรอบ tf

                await read_tf_ticker(ex, spot_symbols)

                next_ticker_tf += time_wait_tf # กำหนดรอบเวลาถัดไป

                break

            await sleep(1)
            print('\r  '+status[count]+' waiting...\r', end='')
            count += 1
            count = count%len(status)

    except KeyboardInterrupt:
        pass

    except Exception as ex:
        print(type(ex).__name__, str(ex))

    await ex.close()

if __name__ == "__main__":
    # Run the main function
    # asyncio.run(main())
    loop = get_event_loop()
    loop.run_until_complete(main())