from application.core.App import App
import asyncio, config
from application.core.Exchange import Binance
from strategy.data_scraper import TradingStrategy
from application.core.record_live_trade import RecordLiveTrade

async def main():
    app = App(
        name = 'App',
        exchange = Binance(api_key=config.API_KEY, api_secret=config.API_SECRET),
        trading_strategy = TradingStrategy(),
        record_trade = RecordLiveTrade('trade_history.csv')
        )
    await app.start()
    await app.run()
    await app.quit()
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
