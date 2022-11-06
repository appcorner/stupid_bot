import plotly.express as px
from datetime import datetime
import pandas as pd
from dataclasses import dataclass
import json

@dataclass
class Trade:
    symbol: str
    time: datetime
    price: float
    quantity: float
    position_side: str

class Account:
    def __init__(self):
        self.position_list = []
        
    def entry_position(self, trade:Trade):
        if self.is_in_account(trade):
            position = self.match_trade_to_position(trade)
            if position.position_side == trade.position_side:
                position.price = (position.price * position.quantity + trade.price * trade.quantity) / (position.quantity + trade.quantity)
                position.quantity += trade.quantity
        else:
            self.position_list.append(trade)
    
    def exit_position(self, trade:Trade):
        position = self.match_trade_to_position(trade)
        if position.quantity*1.001 <= trade.quantity:
            raise ValueError (f'Trade Quantity > Position Quantity on {trade}')
        position.quantity -= trade.quantity
        if trade.position_side == "LONG":
            realized_pnl = trade.quantity * (trade.price-position.price)
        elif trade.position_side == "SHORT":
            realized_pnl = trade.quantity * (-trade.price+position.price)
        self.remove_all_empty_position_account()
        return realized_pnl
    
    def remove_all_empty_position_account(self):
        for position in self.position_list:
            if abs(position.quantity) < 1e-7: self.position_list.remove(position)
    
    def is_in_account(self, trade:Trade):
        in_account = False
        for position in self.position_list:
            if trade.symbol == position.symbol: 
                in_account = True
        return in_account
    
    def match_trade_to_position(self, trade:Trade):
        if self.is_in_account(trade): 
            for position in self.position_list:
                if trade.symbol == position.symbol: 
                    return position
        else:
            raise ValueError (f'We have no {trade.symbol} position! on {trade}')
        
    def display_position(self):
        print('\n')
        for trade in self.position_list:
            print(trade)
    
    def current_open_position(self):
        current_long_position = 0
        current_short_position = 0
        for position in self.position_list:
            if position.position_side == "LONG": current_long_position += 1
            elif position.position_side == "SHORT": current_short_position += 1
        return current_long_position, current_short_position

@dataclass
class PerformanceMetrics:
    long_realized_pnl: float = 0.0
    short_realized_pnl: float = 0.0
    net_realized_pnl: float = 0.0
    long_tradecount: int = 0
    short_tradecount: int = 0
    net_tradecount: int = 0
    current_long_position: int = 0
    current_short_position: int = 0
    
    def display(self):
        for key in self.__dict__: print(f'{key}\t: {self.__dict__[key]}')
    
    def update_net(self):
        self.net_realized_pnl = self.long_realized_pnl + self.short_realized_pnl
        self.net_tradecount = self.long_tradecount + self.short_tradecount

'''
in json file reading mode -> pass in    json_file
in realtime mode -> pass in       order_history, prev_order_history
'''

class PerformanceData:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.tracked_order_name = kwargs['tracked_order_name']
        self.metrics = PerformanceMetrics()
        self.account = Account()
        self.prepare_blank_column()
        self.prepare_start_row()

    def df_order_history(self):
        if 'json_file' in self.kwargs:
            json_file = self.kwargs['json_file']
            self.file_name = f'{json_file}_{self.tracked_order_name}.json'
            self.df = pd.read_json(json_file, orient='index')
        elif 'order_history' in self.kwargs:
            self.df = self.kwargs['order_history'].copy()

    def run(self):
        for i in range(self.start_row-1,-1,-1):
            if self.is_trade_row(i):
                if self.is_long_row(i) and self.is_buy_row(i):
                    self.calculate_each_TRADE_BUY_LONG_row(i)
                elif self.is_long_row(i) and self.is_sell_row(i):
                    self.calculate_each_TRADE_SELL_LONG_row(i)
                elif self.is_short_row(i) and self.is_buy_row(i):
                    self.calculate_each_TRADE_BUY_SHORT_row(i)
                elif self.is_short_row(i) and self.is_sell_row(i):
                    self.calculate_each_TRADE_SELL_SHORT_row(i)
            self.metrics.update_net()
            self.fill_each_row(i)
    
    def prepare_blank_column(self):
        self.df_order_history()
        self.added_columns = [key for key in self.metrics.__dict__]
        for x in self.added_columns: self.df[x] = 0

    def prepare_start_row(self):
        if 'prev_order_history' in self.kwargs: self.start_row = len(self.df) - len(self.kwargs['prev_order_history'])
        else: self.start_row = len(self.df)
        
    def create_trade_object_from_row(self, i):
        symbol = self.df.loc[i, 'symbol']
        time = self.df.loc[i, 'time']
        position_side = self.df.loc[i, 'position_side']
        price = self.df.loc[i, 'price']
        quantity = abs(self.df.loc[i, 'quantity'])
        return Trade(symbol, time, price, quantity, position_side)
        
    def calculate_each_TRADE_BUY_LONG_row(self, i):
        trade = self.create_trade_object_from_row(i)
        self.account.entry_position(trade)
        self.metrics.current_long_position ,self.metrics.current_short_position = self.account.current_open_position()
        self.metrics.long_tradecount += 1
        
    def calculate_each_TRADE_SELL_LONG_row(self, i):
        trade = self.create_trade_object_from_row(i)
        self.metrics.long_realized_pnl += self.account.exit_position(trade)
        self.metrics.current_long_position ,self.metrics.current_short_position = self.account.current_open_position()
        self.metrics.long_tradecount += 1
        
    def calculate_each_TRADE_BUY_SHORT_row(self, i):
        trade = self.create_trade_object_from_row(i)
        self.metrics.short_realized_pnl += self.account.exit_position(trade)
        self.metrics.current_long_position, self.metrics.current_short_position = self.account.current_open_position()
        self.metrics.short_tradecount += 1
        
    def calculate_each_TRADE_SELL_SHORT_row(self, i):
        trade = self.create_trade_object_from_row(i)
        self.account.entry_position(trade)
        self.metrics.current_long_position, self.metrics.current_short_position = self.account.current_open_position()
        self.metrics.short_tradecount += 1
        
    def fill_each_row(self, i):
        for key in self.metrics.__dict__:
            self.df.loc[i, key] = self.metrics.__dict__[key]
        
    def is_trade_row(self, i):
        is_tracked_order_name = self.df.loc[i, 'order_name'] == self.tracked_order_name if self.tracked_order_name != 'Total' else True
        is_tracked_from_order = self.df.loc[i, 'from_order'] == self.tracked_order_name if self.tracked_order_name != 'Total' else True
        is_trade_row = self.df.loc[i, 'order_event'] == 'TRADE'
        return is_trade_row and (is_tracked_order_name or is_tracked_from_order)
    
    def is_long_row(self, i):
        return self.df.loc[i, 'position_side'] == 'LONG'
    
    def is_buy_row(self, i):
        return self.df.loc[i, 'trade_direction'] == 'BUY'
    
    def is_short_row(self, i):
        return self.df.loc[i, 'position_side'] == 'SHORT'
    
    def is_sell_row(self, i):
        return self.df.loc[i, 'trade_direction'] == 'SELL'

    def export_to_json(self):
        result = self.df.to_json(orient="index")
        parsed = json.loads(result)
        with open(self.file_name, 'w') as f:
            json.dump(parsed, f, indent=4)

class PerformanceChartDrawer:
    def __init__(self, order_name_list, order_history_file_name):
        self.order_history_file_name = order_history_file_name
        self.columns = ['time','order_name','net_realized_pnl','net_tradecount']
        self.order_name_list = order_name_list
        self.df = pd.DataFrame(columns=self.columns)
        self.update_df()

    def update_df(self):
        for name in self.order_name_list:
            data = PerformanceData(json_file=self.order_history_file_name,tracked_order_name=name)
            data.run()
            # data.export_to_json()
            
            df_temp = pd.DataFrame(columns=self.columns)
            for column in self.columns:
                if column == 'order_name': df_temp[column] = name
                else: df_temp[column] = data.df[column]
            df_temp['time'] = pd.to_datetime(df_temp['time'], unit='ms')
            self.df = pd.concat([self.df,df_temp], sort = False)

    def display_chart(self):
        fig = px.line(self.df, x="time", y="net_realized_pnl", color='order_name')
        fig.show()
    
