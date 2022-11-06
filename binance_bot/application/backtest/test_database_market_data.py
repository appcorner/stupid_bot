from datetime import datetime
from unittest import TestCase
from application.backtest.database_market_data import CSVMarketData, DatabaseMarketData
from dataclasses import dataclass
import random, time
import pandas as pd

@dataclass
class Candle:
    symbol: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class TestDatabaseEmptyMarketData(TestCase):
    def setUp(self):
        self.database = DatabaseMarketData(':memory:')
        self.database.setup()
        self.database.create_table()
    
    def tearDown(self):
        self.database.close_connection()

    def test_create_table_with_correct_column(self):
        number_of_columns = len(self.database.get_columns())
        columns_we_want = ['time','symbol','open','high','low','close','volume']
        self.assertEqual(number_of_columns, len(columns_we_want))
        
    def test_clear_table_works(self):
        self.database.clear_table()
        with self.assertRaises(NameError):
            self.database.get_columns()
    
    def test_insert_candle_correctly(self):
        self.database.c.rowcount
        self.assertEqual(-1, self.database.c.rowcount)
        candle = Candle('BTCUSDT', datetime.now(), 1.2, 1.3, 1.4, 1.5, 301.2)
        self.database.insert_candle(candle)
        self.assertEqual(1, self.database.c.rowcount)
        
    def test_get_candles_by_symbol_correctly(self):
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 1.2, 1.3, 1.4, 1.5, 301.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 2.2, 2.3, 2.4, 2.5, 601.2))
        self.database.insert_candle(Candle('ETHUSDT', datetime.now(), 3.2, 3.3, 3.4, 3.5, 701.2))
        btc = self.database.get_candles_by_symbol('BTCUSDT')
        self.assertEqual(2, len(btc))
        eth = self.database.get_candles_by_symbol('ETHUSDT')
        self.assertEqual(1.2, btc.loc[0, 'open'])
        self.assertEqual(2.3, btc.loc[1, 'high'])
        self.assertEqual(2.4, btc.loc[1, 'low'])
        self.assertEqual(3.5, eth.loc[0, 'close'])
        
    def test_parse_datetime_correctly(self):
        time = datetime.now()
        self.database.insert_candle(Candle('BTCUSDT', time, 1.2, 1.3, 1.4, 1.5, 301.2))
        btc = self.database.get_candles_by_symbol('BTCUSDT')
        self.assertEqual(time, btc.loc[0, 'time'])
        
    def test_get_candle_feed_give_correct_rows(self):
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 1.2, 1.3, 1.4, 1.5, 301.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 1.2, 1.3, 1.4, 1.5, 301.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 1.2, 1.3, 1.4, 1.5, 301.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 1.2, 1.3, 1.4, 1.5, 301.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 1.2, 1.3, 1.4, 1.5, 301.2))
        self.assertEqual(3, len(self.database.get_candle_feed('BTCUSDT',0,3)))
        
    def test_get_symbol_list(self):
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 2.2, 2.3, 2.4, 2.5, 601.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 2.2, 2.3, 2.4, 2.5, 601.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 2.2, 2.3, 2.4, 2.5, 601.2))
        self.database.insert_candle(Candle('ETHUSDT', datetime.now(), 3.2, 3.3, 3.4, 3.5, 701.2))
        symbol_list = self.database.get_symbol_list()
        self.assertIn('BTCUSDT',symbol_list)
        self.assertEqual(2,len(symbol_list))
        
    def test_get_total_candles_for_one_symbol(self):
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 2.2, 2.3, 2.4, 2.5, 601.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 2.2, 2.3, 2.4, 2.5, 601.2))
        self.database.insert_candle(Candle('BTCUSDT', datetime.now(), 2.2, 2.3, 2.4, 2.5, 601.2))
        self.database.insert_candle(Candle('ETHUSDT', datetime.now(), 3.2, 3.3, 3.4, 3.5, 701.2))
        self.database.insert_candle(Candle('ETHUSDT', datetime.now(), 3.2, 3.3, 3.4, 3.5, 701.2))
        self.database.insert_candle(Candle('ETHUSDT', datetime.now(), 3.2, 3.3, 3.4, 3.5, 701.2))
        self.assertEqual(3, self.database.get_total_candles_for_one_symbol())
        
    def test_check_if_symbol_exist(self):
        with self.assertRaises(KeyError):
            self.database.check_if_symbol_exist('dd')
            
class TestDatabaseScrapedMarketData(TestCase):
    def setUp(self):
        self.database = DatabaseMarketData('data_for_test/04_DEC_2021_to_09_DEC_2021.db')
        self.database.setup()
        
    def test_database_has_been_created(self):
        columns_in_db = self.database.get_columns()
        columns_we_want = ['time','symbol','open','high','low','close','volume']
        self.assertEqual(len(columns_we_want), len(columns_in_db))

    def test_database_has_been_filled(self):
        self.assertGreater(len(self.database.get_symbol_list()),0)
        
    def test_database_has_various_symbols(self):
        symbol_list_in_db = self.database.get_symbol_list()
        symbol_list_we_want = ['XRPUSDT','GALAUSDT','TOMOUSDT','LRCUSDT']
        for symbol in symbol_list_we_want:
            self.assertIn(symbol, symbol_list_in_db)
            
    def test_feed_should_have_correct_index(self):
        symbol_list_in_db = self.database.get_symbol_list()
        def random_(): 
            return random.randint(0, len(symbol_list_in_db)-1)
        df_1 = self.database.get_candle_feed(symbol_list_in_db[random_()], 0, 10)
        df_2 = self.database.get_candle_feed(symbol_list_in_db[random_()], 0, 10)
        self.assertEqual(df_1.loc[0,'time'].minute,df_2.loc[0,'time'].minute)
        df_1 = self.database.get_candle_feed(symbol_list_in_db[random_()], 30, 10)
        df_2 = self.database.get_candle_feed(symbol_list_in_db[random_()], 30, 10)
        self.assertEqual(df_1.loc[0,'time'].minute,df_2.loc[0,'time'].minute)
        
    def test_feed_index0_should_have_most_recent_time(self):
        symbol_list_in_db = self.database.get_symbol_list()
        df = self.database.get_candle_feed(symbol_list_in_db[3], 15, 10)
        self.assertLess(df.loc[1,'time'],df.loc[0,'time'])
        self.assertLess(df.loc[5,'time'],df.loc[4,'time'])
        self.assertLess(df.loc[7,'time'],df.loc[2,'time'])

import os

class TestCSVMarketData(TestCase):
    def setUp(self):
        self.database = CSVMarketData(['data_for_test','test_do_not_put_files_here'])
        self.symbol_list = ['TOMOUSDT','GALAUSDT','LRCUSDT','XRPUSDT']
    
    def tearDown(self):
        self.database.clear_all_csv_files()
    
    def random_symbol(self):
        return self.symbol_list[random.randint(0,len(self.symbol_list)-1)]
    
    def create_random_symbol_df(self):
        symbol = self.random_symbol()
        df = pd.read_json(os.path.join('data_for_test','jsons',f'{symbol}.json'), orient='index')
        self.database.create_csv(symbol,df)
        return symbol
    
    def test_scan_csv_files_list_method_return_file_list(self):
        files_list = self.database.scan_csv_files_list()
        self.assertEqual(type(files_list),type([]))
        symbol = self.create_random_symbol_df()
        files_list = self.database.scan_csv_files_list()
        self.assertEqual(1,len(files_list))
        self.assertEqual(symbol, files_list[0].split('.')[0])
    
    def test_create_csv_method_can_create_csv(self):
        symbol = self.create_random_symbol_df()
        file_exists = os.path.isfile(os.path.join(self.database.path,f'{symbol}.csv'))
        self.assertTrue(file_exists)
        
    def test_read_csv_method_create_with_correct_info(self):
        symbol = self.create_random_symbol_df()
        self.database.prepare_data_on_memory(symbol)
        df = self.database.get_candles_by_symbol(symbol)
        self.assertGreater(len(df),1)
        self.assertEqual(len(self.database.get_columns()),len(df.columns))
        self.assertGreater(df.loc[0,'time'],df.loc[1,'time'])
        
    def test_get_symbol_list(self):
        self.create_random_symbol_df()
        self.create_random_symbol_df()
        symbol_list_actual = [x.split('.')[0] for x in self.database.scan_csv_files_list()]
        symbol_list_from_method = self.database.get_symbol_list()
        self.assertTrue(2, len(symbol_list_from_method))
        for symbol in symbol_list_from_method:
            self.assertTrue(symbol in symbol_list_actual)
            self.assertTrue('USDT' in symbol)
            self.assertFalse('.csv' in symbol)
            
    def test_get_total_candles_for_one_symbol(self):
        symbol = self.create_random_symbol_df()
        self.database.prepare_data_on_memory(symbol)
        self.assertLess(10,self.database.get_total_candles_for_one_symbol())
        
    def test_feed_index0_should_have_most_recent_time(self):
        symbol = self.create_random_symbol_df()
        self.database.prepare_data_on_memory(symbol)
        df = self.database.get_candle_feed(symbol, 15, 10)
        self.assertLess(df.loc[1,'time'],df.loc[0,'time'])
        self.assertLess(df.loc[5,'time'],df.loc[4,'time'])
        self.assertLess(df.loc[7,'time'],df.loc[2,'time'])
        
    def test_check_if_symbol_exist(self):
        with self.assertRaises(KeyError):
            self.database.check_if_symbol_exist('XRPUSDT')
        symbol = self.create_random_symbol_df()
        self.database.check_if_symbol_exist(symbol)