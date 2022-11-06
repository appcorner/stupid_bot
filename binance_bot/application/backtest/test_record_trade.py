from unittest.case import TestCase
from unittest.mock import MagicMock
from application.backtest.database_market_data import CSVMarketData
from application.backtest.record_trade import RecordTrade
import pandas as pd
from application.core import Event

def LongEntry_MarketOrder(symbol, quantity, order_name=''):
    Event.on_send_order.notify(order_type="MARKET", position_side="LONG", trade_direction="BUY",symbol=symbol, quantity=quantity, order_name=order_name)

def ShortEntry_MarketOrder(symbol, quantity, order_name=''):
    Event.on_send_order.notify(order_type="MARKET", position_side="SHORT", trade_direction="SELL",symbol=symbol, quantity=quantity, order_name=order_name)
    
def LongExit_MarketOrder(symbol, quantity, order_name=''):
    Event.on_send_order.notify(order_type="MARKET", position_side="LONG", trade_direction="SELL",symbol=symbol, quantity=quantity, order_name=order_name)

def ShortExit_MarketOrder(symbol, quantity, order_name=''):
    Event.on_send_order.notify(order_type="MARKET", position_side="SHORT", trade_direction="BUY",symbol=symbol, quantity=quantity, order_name=order_name)

def Close_All_Position(portfolio_data):
    long_symbol = portfolio_data[portfolio_data['long_inventory']>0].index
    short_symbol = portfolio_data[portfolio_data['short_inventory']>0].index
    for symbol in long_symbol:
        if portfolio_data['long_inventory'][symbol] == 0: break
        LongExit_MarketOrder(symbol, portfolio_data['long_inventory'][symbol])
    for symbol in short_symbol:
        if portfolio_data['short_inventory'][symbol] == 0: break
        ShortExit_MarketOrder(symbol, portfolio_data['short_inventory'][symbol])

class TestRecordTrade(TestCase):
    def setUp(self):
        self.record_trade = RecordTrade(0.0 ,0.0)
        Event.on_send_order += self.backtest_app_record_order
        self.record_trade.create_tables()
        self.symbol_list = ['TOMOUSDT','GALAUSDT','LRCUSDT','XRPUSDT']
        self.market_data_start_index = 20
        self.update_market_data()
        
    def tearDown(self):
        Event.on_send_order -= self.backtest_app_record_order
    
    def backtest_app_record_order(self, **kwargs):
        self.record_trade.record_order(self.market_data, **kwargs)
    
    def update_market_data(self):
        market_data = {}
        for symbol in self.symbol_list:
            data = CSVMarketData(['data_for_test','04_DEC_2021_to_09_DEC_2021'])
            data.prepare_data_on_memory(symbol)
            market_data[symbol] = data.get_candle_feed(symbol,self.market_data_start_index,15)
        self.market_data = market_data
        self.market_data_start_index += 1

    def test_tables_should_be_created(self):
        self.assertIsNotNone(self.record_trade.portfolio_data)
        self.assertIsNotNone(self.record_trade.trade_history)
        self.assertIsNotNone(self.market_data)
   
    def test_portfolio_data_is_updated_after_order_fired(self):
        self.assertEqual(0, len(self.record_trade.portfolio_data))
        ShortEntry_MarketOrder('XRPUSDT',1.1,'test')
        self.assertEqual(1, len(self.record_trade.portfolio_data))
        ShortExit_MarketOrder('XRPUSDT',1.0,'test')
        self.assertEqual(1, len(self.record_trade.portfolio_data))
        LongEntry_MarketOrder('GALAUSDT',5,'test')
        self.assertEqual(2, len(self.record_trade.portfolio_data))
        
    def test_portfolio_data_is_updated_with_correct_info(self):
        ShortEntry_MarketOrder('XRPUSDT',1.1,'test')
        self.assertAlmostEqual(self.record_trade.portfolio_data.loc['XRPUSDT']['long_inventory'],0)
        self.assertAlmostEqual(self.record_trade.portfolio_data.loc['XRPUSDT']['short_inventory'],1.1)
        ShortExit_MarketOrder('XRPUSDT',1.0,'test')
        self.assertAlmostEqual(self.record_trade.portfolio_data.loc['XRPUSDT']['long_inventory'],0)
        self.assertAlmostEqual(self.record_trade.portfolio_data.loc['XRPUSDT']['short_inventory'],0.1)
        LongEntry_MarketOrder('XRPUSDT',3.2,'test')
        self.assertAlmostEqual(self.record_trade.portfolio_data.loc['XRPUSDT']['long_inventory'],3.2)
        self.assertAlmostEqual(self.record_trade.portfolio_data.loc['XRPUSDT']['short_inventory'],0.1)
        LongExit_MarketOrder('XRPUSDT',1.2,'test')
        self.assertAlmostEqual(self.record_trade.portfolio_data.loc['XRPUSDT']['long_inventory'],2.0)
        self.assertAlmostEqual(self.record_trade.portfolio_data.loc['XRPUSDT']['short_inventory'],0.1)
        
    def test_portfolio_data_raise_error_when_exit_order_is_higher_than_portfolio(self):
        with self.assertRaises(ValueError):
            LongEntry_MarketOrder('XRPUSDT',3.2,'test')
            LongExit_MarketOrder('XRPUSDT',4.2,'test')
        with self.assertRaises(ValueError):
            ShortEntry_MarketOrder('GALAUSDT',3.2,'test')
            ShortExit_MarketOrder('GALAUSDT',4.2,'test')
            
    def test_trade_history_is_updated_after_entry_trade(self):
        LongEntry_MarketOrder('XRPUSDT',3.2,'test')
        self.assertEqual(1, len(self.record_trade.trade_history))
        LongEntry_MarketOrder('GALAUSDT',1.2,'test')
        self.assertEqual(2, len(self.record_trade.trade_history))
        
    def test_catch_matched_open_trade_can_catch_new_trade(self):
        self.record_trade.manage_trade_history.update_trade_row = MagicMock()
        ShortEntry_MarketOrder('GALAUSDT',1.2,'test')
        self.record_trade.manage_trade_history.update_trade_row.assert_not_called()
        ShortExit_MarketOrder('GALAUSDT',1.1,'test')
        self.record_trade.manage_trade_history.update_trade_row.assert_called_once()
        LongEntry_MarketOrder('XRPUSDT',3.2,'test')
        self.record_trade.manage_trade_history.update_trade_row.assert_called_once()
        
    def test_trade_history_is_updated_with_correct_info(self):
        ShortEntry_MarketOrder('GALAUSDT',1.2,'test')
        ShortEntry_MarketOrder('GALAUSDT',1.1,'test')
        self.assertEqual(self.record_trade.trade_history.loc[0,'trade_direction'],'Short')
        self.assertEqual(self.record_trade.trade_history.loc[0,'symbol'],'GALAUSDT')
        self.assertEqual(self.record_trade.trade_history.loc[0,'order_name'],'test')
        self.assertIsNotNone(self.record_trade.trade_history.loc[0,'entry_time'])
        self.assertIsNone(self.record_trade.trade_history.loc[0,'exit_time'])
        self.assertNotEqual(self.record_trade.trade_history.loc[0,'entry_price'],0)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'exit_price'],0)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'remaining_quantity'],2.3)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'quantity'],2.3)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'profit'],0)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'profit_pct'],0)
        ShortExit_MarketOrder('GALAUSDT',2.1,'test')
        self.assertIsNotNone(self.record_trade.trade_history.loc[0,'exit_time'])
        self.assertNotEqual(self.record_trade.trade_history.loc[0,'entry_price'],0)
        self.assertNotEqual(self.record_trade.trade_history.loc[0,'exit_price'],0)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'remaining_quantity'],0.2)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'quantity'],2.3)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'profit'],0)
        self.assertAlmostEqual(self.record_trade.trade_history.loc[0,'profit_pct'],0)
    
    def test_get_single_trade_history_row_from_trade_history(self):
        LongEntry_MarketOrder('XRPUSDT',1.5,'test')
        ShortEntry_MarketOrder('GALAUSDT',1.8,'test')
        trade_row_XRP = self.record_trade.manage_trade_history.get_single_trade_history_row(1)
        trade_row_GALA = self.record_trade.manage_trade_history.get_single_trade_history_row(0)
        self.assertEqual(trade_row_XRP.trade_direction, 'Long')
        self.assertEqual(trade_row_XRP.symbol, 'XRPUSDT')
        self.assertEqual(trade_row_XRP.quantity, 1.5)
        self.assertEqual(trade_row_GALA.trade_direction, 'Short')
        self.assertEqual(trade_row_GALA.symbol, 'GALAUSDT')
        self.assertEqual(trade_row_GALA.quantity, 1.8)
        
    def test_trade_history_rows_should_be_added_when_same_symbol_is_traded_again(self):
        self.assertEqual(0, len(self.record_trade.trade_history))
        LongEntry_MarketOrder('XRPUSDT',1.5,'test')
        ShortEntry_MarketOrder('GALAUSDT',1.8,'test')
        self.assertEqual(2, len(self.record_trade.trade_history))
        LongExit_MarketOrder('XRPUSDT',1.5,'test')
        ShortExit_MarketOrder('GALAUSDT',1.8,'test')
        self.assertEqual(2, len(self.record_trade.trade_history))
        LongEntry_MarketOrder('XRPUSDT',1.5,'test')
        ShortEntry_MarketOrder('GALAUSDT',1.8,'test')
        self.assertEqual(4, len(self.record_trade.trade_history))

    def test_trade_history_should_update_profit_and_loss_correctly(self):
        LongEntry_MarketOrder('XRPUSDT',1.5,'test')
        ShortEntry_MarketOrder('GALAUSDT',1.8,'test')
        ShortEntry_MarketOrder('GALAUSDT',0.3,'test')
        self.update_market_data()
        self.update_market_data()
        self.update_market_data()
        self.update_market_data()
        self.update_market_data()
        # XRPUSDT will be at index 1, GALAUSDT will be at index 0
        LongExit_MarketOrder('XRPUSDT',1.2,'test')
        LongExit_MarketOrder('XRPUSDT',0.3,'test')
        ShortExit_MarketOrder('GALAUSDT',2.1,'test')
        self.assertAlmostEqual((0.51188-0.52353)*2.1, self.record_trade.trade_history.loc[0, 'profit'])
        self.assertAlmostEqual((1-0.52353/0.51188), self.record_trade.trade_history.loc[0, 'profit_pct'])
        self.assertAlmostEqual((0.9036-0.9094)*1.5, self.record_trade.trade_history.loc[1, 'profit'])
        self.assertAlmostEqual((0.9036/0.9094-1), self.record_trade.trade_history.loc[1, 'profit_pct'])
        
    def test_trade_history_should_calculate_max_drawdown_runup_correctly(self):
        entry_price_XRP = self.market_data['XRPUSDT'].loc[0,'close']
        entry_price_GALA = self.market_data['GALAUSDT'].loc[0,'close']
        LongEntry_MarketOrder('XRPUSDT',1.5,'test')
        ShortEntry_MarketOrder('GALAUSDT',1.8,'test')
        ShortEntry_MarketOrder('GALAUSDT',0.3,'test')
        self.update_market_data()
        self.record_trade.update_on_candle(self.market_data)
        self.update_market_data()
        self.record_trade.update_on_candle(self.market_data)
        self.update_market_data()
        self.record_trade.update_on_candle(self.market_data)
        self.update_market_data()
        self.record_trade.update_on_candle(self.market_data)
        self.update_market_data()
        self.record_trade.update_on_candle(self.market_data)
        # XRPUSDT will be at index 1, GALAUSDT will be at index 0
        LongExit_MarketOrder('XRPUSDT',1.2,'test')
        LongExit_MarketOrder('XRPUSDT',0.3,'test')
        ShortExit_MarketOrder('GALAUSDT',2.1,'test')
        high_XRP = max(self.market_data['XRPUSDT'][0:4]['high'].max(),entry_price_XRP)
        low_XRP = min(self.market_data['XRPUSDT'][0:4]['low'].min(),entry_price_XRP)        
        high_GALA = max(self.market_data['GALAUSDT'][0:4]['high'].max(),entry_price_GALA)
        low_GALA = min(self.market_data['GALAUSDT'][0:4]['low'].min(),entry_price_GALA)
        self.assertAlmostEqual((entry_price_GALA-high_GALA)*2.1, self.record_trade.trade_history.loc[0, 'max_drawdown'])
        self.assertAlmostEqual((entry_price_GALA-low_GALA)*2.1, self.record_trade.trade_history.loc[0, 'max_runup'])
        self.assertAlmostEqual((low_XRP-entry_price_XRP)*1.5, self.record_trade.trade_history.loc[1, 'max_drawdown'])
        self.assertAlmostEqual((high_XRP-entry_price_XRP)*1.5, self.record_trade.trade_history.loc[1, 'max_runup'])

class TestCommissionSlippage(TestCase):
    def setUp(self):
        self.record_trade = RecordTrade(0.1 ,0.2)
        Event.on_send_order += self.backtest_app_record_order
        self.record_trade.create_tables()
        self.symbol_list = ['TOMOUSDT','GALAUSDT','LRCUSDT','XRPUSDT']
        self.market_data_start_index = 20
        self.update_market_data()
        
    def tearDown(self):
        Event.on_send_order -= self.backtest_app_record_order
    
    def backtest_app_record_order(self, **kwargs):
        self.record_trade.record_order(self.market_data, **kwargs)
    
    def update_market_data(self):
        market_data = {}
        for symbol in self.symbol_list:
            data = CSVMarketData(['data_for_test','04_DEC_2021_to_09_DEC_2021'])
            data.prepare_data_on_memory(symbol)
            market_data[symbol] = data.get_candle_feed(symbol,self.market_data_start_index,15)
        self.market_data = market_data
        self.market_data_start_index += 1
        
    def test_commission_slippage_is_calculated_correctly(self):
        LongEntry_MarketOrder('XRPUSDT',1.4,'test')
        ShortEntry_MarketOrder('LRCUSDT',1.8,'test')
        close_price_XRP = self.market_data['XRPUSDT'].loc[0,'close']
        entry_price_XRP = close_price_XRP * 1.001 * 1.002
        close_price_LRC = self.market_data['LRCUSDT'].loc[0,'close']
        entry_price_LRC = close_price_LRC * 0.999 * 0.998
        self.assertAlmostEqual(entry_price_LRC, self.record_trade.trade_history.loc[0, 'entry_price'])        
        self.assertAlmostEqual(entry_price_XRP, self.record_trade.trade_history.loc[1, 'entry_price'])
        
        self.update_market_data()
        self.update_market_data()
        self.update_market_data()
        self.update_market_data()
        self.update_market_data()
        
        LongExit_MarketOrder('XRPUSDT',1.4,'test')
        ShortExit_MarketOrder('LRCUSDT',1.8,'test')
        close_price_XRP = self.market_data['XRPUSDT'].loc[0,'close']
        exit_price_XRP = close_price_XRP * 0.999 * 0.998
        close_price_LRC = self.market_data['LRCUSDT'].loc[0,'close']
        exit_price_LRC = close_price_LRC * 1.001 * 1.002
        self.assertAlmostEqual(exit_price_LRC, self.record_trade.trade_history.loc[0, 'exit_price'])        
        self.assertAlmostEqual(exit_price_XRP, self.record_trade.trade_history.loc[1, 'exit_price'])
        
    def test_get_most_traded_symbol(self):
        LongEntry_MarketOrder('XRPUSDT',1.0,'test')
        LongEntry_MarketOrder('LRCUSDT',1.0,'test')
        LongEntry_MarketOrder('GALAUSDT',1.0,'test')
        self.update_market_data
        LongExit_MarketOrder('XRPUSDT',1.0,'test')
        LongExit_MarketOrder('LRCUSDT',1.0,'test')
        LongExit_MarketOrder('GALAUSDT',1.0,'test')
        self.update_market_data
        LongEntry_MarketOrder('XRPUSDT',1.0,'test')
        self.update_market_data
        LongExit_MarketOrder('XRPUSDT',1.0,'test')
        symbol = self.record_trade.manage_trade_history.get_most_traded_symbol()
        self.assertEqual(symbol, 'XRPUSDT')