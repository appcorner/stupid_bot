import asyncio
from application.analysis.draw_charts import TradeActivitySingleSymbol
from application.backtest.backtest_app import BacktestApp


class App:
    def __init__(self, feed_data, trading_strategy, record_trade):
        self.feed_data = feed_data
        self.trading_strategy = trading_strategy
        self.record_trade = record_trade
        
    def perform_feasibility_analysis(self, path_to_save_trading_history_in_list):
        trading_history, symbol, most_traded_symbol_market_data = self.run_backtest(path_to_save_trading_history_in_list)
        self.see_trade_activity_for_single_symbol(trading_history, self.trading_strategy, symbol, most_traded_symbol_market_data)
        self.perform_montecarlo_shuffling_test(trading_history)
        self.perform_montecarlo_resampling_test(trading_history)
    
    def run_backtest(self, path_to_save_trading_history_in_list):
        backtest_app = BacktestApp(self.trading_strategy, self.feed_data, self.record_trade)
        asyncio.run(backtest_app.setup())
        asyncio.run(backtest_app.run())
        backtest_app.display_result()
        backtest_app.export_result_to_csv(path_to_save_trading_history_in_list)
        symbol, single_symbol_market_data = backtest_app.get_most_traded_symbol_from_trading_history()
        return backtest_app.trade_history, symbol, single_symbol_market_data

    @staticmethod
    def see_trade_activity_for_single_symbol(trading_history, trading_strategy, symbol, most_traded_symbol_market_data):
        '''
        objective: to check if our trading strategy is coded correctly as we expect
        input: market_data, trading_strategy
        output: trade_activity chart -> chart with indicators, candlesticks, buy-sell actions
        '''
        trade_activity_for_single_symbol = TradeActivitySingleSymbol(trading_history, trading_strategy, symbol, most_traded_symbol_market_data)
        trade_activity_for_single_symbol.prepare_data()
        trade_activity_for_single_symbol.display_chart()
    
    @staticmethod
    def perform_montecarlo_shuffling_test(trading_history, number_of_simulations = 100, pct_to_randomly_remove_data = 0.1):
        '''
        objective: to determine worst draw down we might encouter during this backtest
        input: trading strategy, market_data
        output: equity-trade chart
        '''
        pass
    
    @staticmethod
    def perform_montecarlo_resampling_test(trading_history, number_of_simulations = 100):
        '''
        objective: to determine expected profit ranges
        input: trading strategy, market_data
        output: equity-trade chart
        '''
        pass
    
    def perform_out_of_sample_testing(self, number_of_backtest_samples = 10, pct_the_length_of_testing_for_each_sample = 0.25):
        '''
        input: trading strategy, market_data
        output: equity-trade chart(s)
        '''
        pass
    
    def perform_walk_forward_analysis(self):
        '''
        input: trading strategy, market_data, parameters to optimize
        output: optimized parameters, equity-trade chart
        '''
        pass
    
    def perform_clustered_walk_forward_analysis(self):
        '''
        input: trading strategy, market_data, parameters to optimize
        output: optimized parameters, equity-trade chart
        '''
        pass