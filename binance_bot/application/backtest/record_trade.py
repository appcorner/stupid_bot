from application.backtest.record_trade_display import CalculateTradeStatistics
from application.backtest.record_trade_tables import ManagePortfolioData, ManageTradeHistory, TradeType

class RecordTrade:
    def __init__(self, commission, slippage):
        self.commission = commission
        self.slippage = slippage
        self.manage_portfolio_data = ManagePortfolioData()
        self.manage_trade_history = ManageTradeHistory()

    def create_tables(self):
        self.portfolio_data = self.manage_portfolio_data.df
        self.trade_history = self.manage_trade_history.df
        return self.portfolio_data, self.trade_history
    
    def record_order(self, market_data, **kwargs):
        time = market_data[kwargs['symbol']].at[0,'time']
        entry_price, trade_side = self.process_trade(market_data[kwargs['symbol']].at[0,'close'],**kwargs)
        self.portfolio_data = self.manage_portfolio_data.update(kwargs['symbol'], kwargs['quantity'], trade_side)
        self.trade_history = self.manage_trade_history.update(time, trade_side, entry_price, **kwargs)

    def finalize_result(self):
        self.finalize_trade_stats = CalculateTradeStatistics(self.trade_history)
        self.finalize_trade_stats.perform_calculation()
        return self.finalize_trade_stats.result()

    def export_result(self, path):
        self.trade_history.to_csv(path)
    
    def categorize_trade(self, **kwargs):
        if not kwargs['order_type'] == 'MARKET': raise KeyError('Our Backtest only supports Market Orders')
        if kwargs['trade_direction'] == 'BUY' and kwargs['position_side'] == 'LONG': trade_side = TradeType.LongEntry
        elif kwargs['trade_direction'] == 'SELL' and kwargs['position_side'] == 'LONG': trade_side = TradeType.LongExit
        elif kwargs['trade_direction'] == 'SELL' and kwargs['position_side'] == 'SHORT': trade_side = TradeType.ShortEntry
        elif kwargs['trade_direction'] == 'BUY' and kwargs['position_side'] == 'SHORT': trade_side = TradeType.ShortExit
        return trade_side
        
    def process_trade(self, close_price, **kwargs):
        trade_side = self.categorize_trade(**kwargs)
        if trade_side == TradeType.LongEntry or trade_side == TradeType.ShortExit:
            entry_price = close_price * (100 + self.commission) / 100 * (100 + self.slippage) / 100
        elif trade_side == TradeType.LongExit or trade_side == TradeType.ShortEntry:
            entry_price = close_price * (100 - self.commission) / 100 * (100 - self.slippage) / 100
        return entry_price, trade_side
    
    def update_on_candle(self, market_data):
        self.trade_history = self.manage_trade_history.update_on_candle(market_data)
        return self.portfolio_data, self.trade_history
    
    def get_most_traded_symbol(self):
        return self.manage_trade_history.get_most_traded_symbol()