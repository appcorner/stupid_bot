import asyncio
from application.backtest.backtest_app import BacktestApp
from application.backtest.feed_data import FeedData
from application.backtest.record_trade import RecordTrade
from strategy.simple_strategy import TradingStrategy
import cProfile
import pstats


def main():
    App =BacktestApp(trading_strategy = TradingStrategy(),
                    feed_data = FeedData(['data_for_test','04_DEC_2021_to_09_DEC_2021']),
                    record_trade = RecordTrade(0.0,0.0))
    asyncio.run(App.setup())

    # with cProfile.Profile() as pr:
    #     asyncio.run(App.run())
    # stats = pstats.Stats(pr)
    # stats.sort_stats(pstats.SortKey.TIME)
    # stats.dump_stats(filename='profiling.prof')

    App.display_result()
    App.export_result_to_csv(['data_for_test','trade_history.csv'])
    
if __name__ == '__main__':
    main()