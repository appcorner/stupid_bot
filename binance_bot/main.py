from application.core.App import App
from application.core import Event
from application.core.record_live_trade import RecordLiveTrade
import asyncio, config
from application.core.Exchange import Binance
from strategy.relative_strength import TradingStrategy
import time, os, sys

async def main():
    app = App(
        name = 'App',
        exchange = Binance(api_key=config.API_KEY, api_secret=config.API_SECRET),
        trading_strategy = TradingStrategy(),
        record_trade = RecordLiveTrade(['record_live_trade','my_trade.csv'])
        )
    try:
        await asyncio.gather(
            run_app(app),
            shutdown(3600)
        )
    except TimeoutError:
        await app.quit()

async def run_app(app):
    await app.start()
    await app.run()

async def shutdown(time_limit_seconds):
    await asyncio.sleep(time_limit_seconds)
    await Event.on_app_shutdown.async_notify()
    raise TimeoutError
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    time.sleep(15)
    os.execv(sys.executable, [sys.executable, __file__] + sys.argv)
