import os
from unittest import TestCase

import pandas as pd
from application.core.record_live_trade import RecordLiveTrade


class TestRecordLiveTrade(TestCase):
    def setUp(self):
        self.record_live_trade = RecordLiveTrade(['data_for_test','test_do_not_put_files_here','trade_history.csv'])
        feed_order_history_path = os.path.join('data_for_test','jsons','order_history_02Dec2021_0908.json')
        self.feed_order_history = pd.read_json(feed_order_history_path, orient='index')
        self.record_live_trade.create_tables()
        
    def test_tables_should_be_created(self):
        self.assertIsNotNone(self.record_live_trade.portfolio_data)
        self.assertIsNotNone(self.record_live_trade.trade_history)
        
    def test_record_order_can_catch_order_history_feed(self):
        self.record_live_trade.record_order(self.feed_order_history)
        self.assertEqual(0,len(self.record_live_trade.portfolio_data))
        self.assertEqual(0,len(self.record_live_trade.trade_history))
        self.feed_order_history.index -= 1
        self.record_live_trade.record_order(self.feed_order_history)
        self.assertEqual(1,len(self.record_live_trade.portfolio_data))
        self.assertEqual(1,len(self.record_live_trade.trade_history))
        self.feed_order_history.index -= 1
        self.record_live_trade.record_order(self.feed_order_history)
        self.assertEqual(1,len(self.record_live_trade.portfolio_data))
        self.assertEqual(1,len(self.record_live_trade.trade_history))
        self.feed_order_history.index -= 1
        self.record_live_trade.record_order(self.feed_order_history)
        self.assertEqual(2,len(self.record_live_trade.portfolio_data))
        self.assertEqual(2,len(self.record_live_trade.trade_history))
    
    
        
    