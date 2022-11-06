import os
from application.backtest.record_trade_tables import TradeType, ManagePortfolioData, ManageTradeHistory, TradeType
from application.backtest.record_trade_display import CalculateTradeStatistics
import pandas as pd

class RecordLiveTrade():
    def __init__(self,trade_history_path):
        self.trade_history_path = os.path.join(*trade_history_path)
        self.manage_portfolio_data = ManagePortfolioData()
        self.manage_trade_history = ManageTradeHistory()
    
    def create_tables(self):
        try :
            self.trade_history = pd.read_csv(self.trade_history_path,index_col=0)
        except FileNotFoundError:
            self.trade_history = self.manage_trade_history.df
        self.portfolio_data = self.manage_portfolio_data.df
        return self.portfolio_data, self.trade_history

    def record_order(self, order_history):
        if order_history.at[0,'order_event'] == 'TRADE':
            time = order_history.at[0,'time']
            symbol = order_history.at[0,'symbol']
            price = float(order_history.at[0,'price'])
            quantity = float(order_history.at[0,'quantity'])
            trade_side = self.categorize_trade(trade_direction = order_history.at[0,'trade_direction'], 
                                            position_side = order_history.at[0,'position_side'])
            self.portfolio_data = self.manage_portfolio_data.update(symbol, quantity, trade_side)
            self.trade_history = self.manage_trade_history.update(time, 
                                                                trade_side, 
                                                                price, 
                                                                symbol=symbol, 
                                                                order_name=order_history.at[0,'order_name'],
                                                                quantity = quantity, 
                                                                remaining_quantity = quantity)
        return self.portfolio_data, self.trade_history

    def finalize_result(self):
        self.finalize_trade_stats = CalculateTradeStatistics(self.trade_history)
        self.finalize_trade_stats.perform_calculation()
        return self.finalize_trade_stats

    def export_result(self):
        self.trade_history.to_csv(self.trade_history_path)
        
    def categorize_trade(self, **kwargs):
        if kwargs['trade_direction'] == 'BUY' and kwargs['position_side'] == 'LONG': trade_side = TradeType.LongEntry
        elif kwargs['trade_direction'] == 'SELL' and kwargs['position_side'] == 'LONG': trade_side = TradeType.LongExit
        elif kwargs['trade_direction'] == 'SELL' and kwargs['position_side'] == 'SHORT': trade_side = TradeType.ShortEntry
        elif kwargs['trade_direction'] == 'BUY' and kwargs['position_side'] == 'SHORT': trade_side = TradeType.ShortExit
        return trade_side
    
    def update_on_candle(self, market_data):
        self.trade_history = self.manage_trade_history.update_on_candle(market_data)
        return self.portfolio_data, self.trade_history
