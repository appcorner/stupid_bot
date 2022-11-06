from datetime import datetime
import sqlite3
import pandas as pd
import os.path

class DatabaseMarketData:
    def __init__(self, path):
        self.path = path
        
    def setup(self):
        self.conn = sqlite3.connect(self.path)
        self.c = self.conn.cursor()
    
    def close_connection(self):
        self.conn.close()
        
    def create_table(self):
        try:
            self.c.execute("""CREATE TABLE MarketData (
            time TEXT,
            symbol TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL
            )""")
        except sqlite3.OperationalError:
            pass

    def clear_table(self):
        self.c.execute("DROP TABLE MarketData")
        
    def get_columns(self):
        try: df = pd.read_sql('SELECT * FROM MarketData', self.conn)
        except pd.io.sql.DatabaseError: raise NameError ('There is no MarketData table in database file')
        return df.columns
    
    def insert_candle(self, candle):
        self.c.execute('INSERT INTO MarketData VALUES (:time,:symbol,:open,:high,:low,:close,:volume)',
                       {'time':candle.time, 'symbol':candle.symbol, 'open':candle.open, 'high':candle.high, 'low':candle.low, 'close':candle.close, 'volume':candle.volume})
        self.conn.commit()
    
    def get_candles_by_symbol(self, symbol):
        df = pd.read_sql(f"SELECT * FROM MarketData WHERE symbol='{symbol}';", self.conn, parse_dates = ['time'])
        return df
    
    def get_symbol_list(self):
        df = pd.read_sql(f"SELECT * FROM MarketData", self.conn, parse_dates = ['time'])
        return df['symbol'].unique()
    
    def get_total_candles_for_one_symbol(self):
        symbol_list = self.get_symbol_list()
        return len(self.get_candles_by_symbol(symbol_list[0]))
    
    def get_candle_feed(self, symbol, start_row, chunk_size):
        df = self.get_candles_by_symbol(symbol)
        return df[start_row : start_row + chunk_size][::-1].reset_index(drop=True)
    
    def check_if_symbol_exist(self, symbol):
        if len(self.get_candles_by_symbol(symbol)) == 0:
            raise KeyError (f'No Data for this symbol: {symbol}')
        
class CSVMarketData:
    def __init__(self, path:list):
        self.path = os.path.join(*path)
        self.columns = ['time','open','high','low','close','volume']
        self.all_candles_data = {}
        
    def setup(self):
        pass
    
    def close_connection(self):
        pass
    
    def create_csv(self, symbol, df):
        df.to_csv(os.path.join(self.path,f'{symbol}.csv'))

    def scan_csv_files_list(self):
        files_list = [f for f in os.listdir(self.path)]
        return files_list
    
    def clear_all_csv_files(self):
        files_list = self.scan_csv_files_list()
        for file in files_list:
            file_path = os.path.join(self.path,file)
            os.remove(file_path)
    
    def prepare_data_on_memory(self, symbol):
        file_path = os.path.join(self.path,f'{symbol}.csv')
        df = pd.read_csv(file_path, index_col = 0, parse_dates=['time'])
        if df.loc[0, 'time'] is not type(datetime): 
            df['time'] = pd.to_datetime(df['time'], unit = 'ms')
        self.all_candles_data[symbol] = df
    
    def get_columns(self):
        return self.columns
    
    def get_candles_by_symbol(self, symbol):
        return self.all_candles_data[symbol]
    
    def get_symbol_list(self):
        return [x.split('.')[0] for x in self.scan_csv_files_list()]
    
    def get_total_candles_for_one_symbol(self):
        symbol_list = self.get_symbol_list()
        self.prepare_data_on_memory(symbol_list[0])
        return len(self.all_candles_data[symbol_list[0]])
    
    def get_candle_feed(self, symbol, start_row, chunk_size):
        df = self.get_candles_by_symbol(symbol)
        return df[start_row : start_row + chunk_size][::-1].reset_index(drop=True)
    
    def check_if_symbol_exist(self, symbol):
        if symbol not in self.get_symbol_list():
            raise KeyError (f'No Data for this symbol: {symbol}')