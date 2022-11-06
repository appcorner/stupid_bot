import os
from application.core import Event

class BacktestApp:
    def __init__(self, trading_strategy, feed_data, record_trade):
        self.trading_strategy = trading_strategy
        self.feed_data = feed_data
        self.record_trade = record_trade
        
    async def setup(self):
        self.feed_data.setup(self.trading_strategy.parameters_on_data.candle_max_length,
                             self.trading_strategy.watch_list)
        self.market_data = self.feed_data.first_feed()
        self.portfolio_data, self.trade_history = self.record_trade.create_tables()
        await self.trading_strategy.on_candle_closed(self.market_data, {}, self.portfolio_data, {}, {}, self.trade_history)
        Event.on_send_order += self.record_order
        
    async def run(self):
        while self.feed_data.is_not_finished():
            self.market_data = self.feed_data.feed()
            self.add_indicators()
            self.portfolio_data, self.trade_history = self.record_trade.update_on_candle(self.market_data)
            await self.trading_strategy.on_candle_closed(self.market_data, {}, self.portfolio_data, {}, {}, self.trade_history)
        await self.trading_strategy.on_app_shutdown(self.market_data, {}, self.portfolio_data, {})
    
    def add_indicators(self):
        for symbol in self.trading_strategy.watch_list:
            df = self.market_data[symbol]
            self.market_data[symbol] = self.trading_strategy.add_indicators(df)
    
    def export_result_to_csv(self, path_in_list):
        '''
        pass in something that looks like this
        path_in_list = ['folder1','folder2','myexcel.csv']
        '''
        path = os.path.join(*path_in_list)
        self.record_trade.export_result(path)
    
    def display_result(self):
        print(self.record_trade.finalize_result())
        
    async def record_order(self, **kwargs):
        self.record_trade.record_order(self.market_data, **kwargs)
        
    def get_most_traded_symbol_from_trading_history(self):
        symbol = self.record_trade.get_most_traded_symbol()
        single_symbol_market_data = self.feed_data.get_all_candles(symbol)
        return symbol, single_symbol_market_data