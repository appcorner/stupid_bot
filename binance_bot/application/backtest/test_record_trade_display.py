import os
from unittest import TestCase
from numpy import float64
import pandas as pd

from application.backtest.record_trade_display import CalculateTradeStatistics

class TestCalculateTradeStatistics(TestCase):
    def setUp(self):
        self.df = pd.read_csv(os.path.join('data_for_test','test','trade_history.csv'),index_col=0)
        self.calculate_trade_stats = CalculateTradeStatistics(self.df)
    
    def test_calculate_profit_correctly(self):
        self.calculate_trade_stats.calculate_profit()
        net_profit = self.calculate_trade_stats.net_profit
        gross_profit = self.calculate_trade_stats.gross_profit
        gross_loss = self.calculate_trade_stats.gross_loss
        self.assertAlmostEqual(net_profit, gross_profit+gross_loss)
        
    def test_calculate_maxmin_correct_type(self):
        self.calculate_trade_stats.calculate_maxmin()
        max_win = self.calculate_trade_stats.max_win
        max_win_pct = self.calculate_trade_stats.max_win_pct
        max_loss = self.calculate_trade_stats.max_loss
        max_loss_pct = self.calculate_trade_stats.max_loss_pct
        self.assertEqual(type(max_win*max_win_pct*max_loss*max_loss_pct),float64)
        
    def test_count_trades(self):
        self.calculate_trade_stats.count_trades()
        total_trades = self.calculate_trade_stats.total_trades
        total_winning_trades = self.calculate_trade_stats.total_winning_trades
        total_losing_trades = self.calculate_trade_stats.total_losing_trades
        self.assertEqual(type(total_trades*total_winning_trades*total_losing_trades),int)
        self.assertLessEqual(total_winning_trades+total_losing_trades,total_trades)
        self.assertLess(self.calculate_trade_stats.pct_protitable_trades,1)
        
    def test_display(self):
        self.calculate_trade_stats.perform_calculation()
        # print(self.calculate_trade_stats.result())