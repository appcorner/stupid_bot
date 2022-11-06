from application.backtest.database_market_data import CSVMarketData


class FeedData:
    def __init__(self, path, start_candle=0, end_candle=None):
        self.database = CSVMarketData(path)
        self.candle_position_now = start_candle
        self.candle_position_end = end_candle
        
    def setup(self, chunk_size, watch_list):
        self.database.setup()
        if self.candle_position_end is None:
            self.candle_position_end = self.database.get_total_candles_for_one_symbol()
        self.chunk_size = chunk_size
        self.watch_list = watch_list
    
    def first_feed(self):
        first_feed = {}
        for symbol in self.watch_list:
            first_feed[symbol] = self.get_first_feed(symbol)
        return first_feed

    def feed(self):
        self.candle_position_now += 1
        feed = {}
        for symbol in self.watch_list:
            feed[symbol] = self.get_feed(symbol)
        return feed
    
    def is_not_finished(self):
        return self.candle_position_now < self.candle_position_end - self.chunk_size
    
    def close(self):
        self.database.close_connection()
    
    def get_first_feed(self, symbol):
        self.database.check_if_symbol_exist(symbol)
        self.database.prepare_data_on_memory(symbol)
        return self.get_feed(symbol)
    
    def get_feed(self, symbol):
        return self.database.get_candle_feed(symbol, self.candle_position_now, self.chunk_size)

    def get_all_candles(self, symbol):
        return self.database.get_candles_by_symbol(symbol)