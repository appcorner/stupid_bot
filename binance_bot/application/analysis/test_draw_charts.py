from datetime import datetime
import os
from unittest import TestCase
import pandas as pd
from application.analysis.draw_charts import TradeActivitySingleSymbol
from strategy.simple_strategy import TradingStrategy

class TestTradeActivitySingleSymbol(TestCase):
    def setUp(self) -> None:
        trading_history_path = ['data_for_test','test','trade_history.csv']
        self.trading_history = pd.read_csv(os.path.join(*trading_history_path),index_col=0, parse_dates=['entry_time','exit_time'])
        self.symbol = self.trading_history['symbol'].mode().at[0]
        single_symbol_market_data_path = ['data_for_test','04_DEC_2021_to_09_DEC_2021',f'{self.symbol}.csv']
        self.single_symbol_market_data = pd.read_csv(os.path.join(*single_symbol_market_data_path),index_col=0, parse_dates=['time'])
        self.trading_strategy = TradingStrategy()
        self.trade_activity_single_symbol = TradeActivitySingleSymbol(self.trading_history, 
                                                                      self.trading_strategy, 
                                                                      self.symbol, 
                                                                      self.single_symbol_market_data)
        
    def test_setup_correctly(self):
        self.assertLess(10, len(self.trading_history))
        self.assertEqual(type('text'),type(self.symbol))
        self.assertLess(10,len(self.single_symbol_market_data))
        
    def test_add_indicators_works(self):
        self.trade_activity_single_symbol.add_indicator()
        self.assertIn('ema',self.trade_activity_single_symbol.df.columns)

    def test_extract_trade_from_trading_history(self):
        trade_list = self.trade_activity_single_symbol.extract_trade_from_trading_history()
        self.assertGreater(len(trade_list), 10)
        self.assertIsInstance(trade_list[0], dict)
        self.assertIsInstance(trade_list[0]['entry_time'], datetime)
        self.assertIsInstance(trade_list[0]['exit_time'], datetime)
        self.assertIsInstance(trade_list[0]['trade_direction'], str)

