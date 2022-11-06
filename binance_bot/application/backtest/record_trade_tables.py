import pandas as pd
from dataclasses import dataclass
from datetime import datetime

class TradeType:
    LongEntry = 'LongEntry'
    LongExit = 'LongExit'
    ShortEntry = 'ShortEntry'
    ShortExit = 'ShortExit'

class TradeDirection:
    Long = 'Long'
    Short = 'Short'
    
@dataclass
class TradeRow:
    trade_direction: TradeDirection=None
    trade_type: TradeType=None
    symbol: str=''
    order_name: str=''
    entry_time: datetime=None
    exit_time: datetime=None
    entry_price: float=0.0
    exit_price: float=0.0
    remaining_quantity: float=0.0
    quantity: float=0.0
    profit: float=0.0
    profit_pct: float=0.0
    max_drawdown: float=0.0
    max_runup: float=0.0
    
    def to_list(self):
        return self.__dict__.values()

class ManageOrderHistory:
    def __init__(self):
        columns = ['time','symbol','order_type','trade_direction','position_side', 'price', 'quantity','order_name']
        self.df = pd.DataFrame(columns = columns)
    
    def update(self,time,price,**kwargs):
        new_order = [time,kwargs['symbol'],kwargs['order_type'],kwargs['trade_direction'],kwargs['position_side'],price,kwargs['quantity'],kwargs['order_name']]
        self.df.loc[-1] = new_order
        self.df.index += 1
        return self.df
    
class ManagePortfolioData:
    def __init__(self):
        columns = ['long_inventory', 'short_inventory']
        self.df = pd.DataFrame(columns = columns)
    
    def update(self, symbol, quantity, trade_side):
        if symbol not in self.df.index:
            long_inventory = quantity if trade_side == TradeType.LongEntry else 0
            short_inventory = quantity if trade_side == TradeType.ShortEntry else 0
        else:
            if trade_side == TradeType.LongEntry:
                long_inventory = self.df.loc[symbol]['long_inventory'] + quantity
                short_inventory = self.df.loc[symbol]['short_inventory']
            elif trade_side == TradeType.LongExit:
                long_inventory = self.df.loc[symbol]['long_inventory'] - quantity
                short_inventory = self.df.loc[symbol]['short_inventory']
            elif trade_side == TradeType.ShortEntry:
                long_inventory = self.df.loc[symbol]['long_inventory']
                short_inventory = self.df.loc[symbol]['short_inventory'] + quantity
            elif trade_side == TradeType.ShortExit:
                long_inventory = self.df.loc[symbol]['long_inventory']
                short_inventory = self.df.loc[symbol]['short_inventory'] - quantity
        long_inventory, short_inventory = self.round_zero_inventory(long_inventory, short_inventory)
        self.df.loc[symbol] = [long_inventory,short_inventory]
        return self.df

    def round_zero_inventory(self, long_inventory, short_inventory):
        if long_inventory < -0.0000001 or short_inventory < -0.0000001 : 
            raise ValueError('Exit order quantity can not be larger than portfolio quantity')
        return round(long_inventory,5), round(short_inventory,5)
    
class ManageTradeHistory:
    def __init__(self):
        self.df = pd.DataFrame(columns = list(TradeRow().__dict__.keys()))
        
    def update(self, time, trade_side, entry_price, **kwargs):
        trade_row = self.create_trade(time, trade_side, entry_price, **kwargs)
        matched_open_trade_row_index = self.catch_matched_open_trade(trade_row)
        if matched_open_trade_row_index == -1 : self.add_new_trade(trade_row)
        else: self.update_trade_row(trade_row, matched_open_trade_row_index)
        return self.df

    def create_trade(self, time, trade_side, entry_price, **kwargs):
        return TradeRow(
            trade_direction = TradeDirection.Long if trade_side == TradeType.LongEntry or trade_side == TradeType.LongExit else TradeDirection.Short,
            trade_type = trade_side,
            symbol = kwargs['symbol'],
            order_name = kwargs['order_name'],
            entry_time = time,
            quantity = kwargs['quantity'],
            remaining_quantity = kwargs['quantity'],
            entry_price = entry_price
        )
    
    def get_open_position_index(self):
        open_position_filter = self.df['remaining_quantity'] > 0
        df = self.df[open_position_filter]
        if len(df.index) == 0: return []
        else: return list(df.index)
    
    def catch_matched_open_trade(self, trade_row: TradeRow):
        open_position_filter = self.df['remaining_quantity'] > 0
        same_symbol_filter = self.df['symbol'] == trade_row.symbol
        df = self.df[open_position_filter & same_symbol_filter]
        if len(df.index) == 0: return -1
        else: return df.index[0]
    
    def add_new_trade(self, trade_row: TradeRow):
        self.df.loc[-1] = trade_row.to_list()
        self.df.index += 1
    
    def update_trade_row(self, new_trade_row: TradeRow, matched_trade_row_index):
        matched_trade_row = self.get_single_trade_history_row(matched_trade_row_index)
        is_exit_trade = new_trade_row.trade_type == TradeType.LongExit or new_trade_row.trade_type == TradeType.ShortExit
        entry_price = matched_trade_row.entry_price if is_exit_trade else (matched_trade_row.entry_price*matched_trade_row.quantity + new_trade_row.entry_price*new_trade_row.quantity)/(matched_trade_row.quantity+new_trade_row.quantity)
        exit_price = new_trade_row.entry_price if is_exit_trade else 0.0
        remaining_quantity = matched_trade_row.remaining_quantity - new_trade_row.quantity if is_exit_trade else matched_trade_row.remaining_quantity + new_trade_row.quantity
        quantity = matched_trade_row.quantity if is_exit_trade else matched_trade_row.quantity + new_trade_row.quantity
        profit = (exit_price - entry_price) * (quantity - remaining_quantity) if matched_trade_row.trade_direction == TradeDirection.Long else (entry_price - exit_price) * (quantity - remaining_quantity)
        profit_pct = profit / (quantity * entry_price)
        updated_trade_row = TradeRow(
            trade_direction = matched_trade_row.trade_direction,
            symbol = matched_trade_row.symbol,
            order_name = matched_trade_row.order_name,
            entry_time = matched_trade_row.entry_time,
            exit_time = new_trade_row.entry_time if is_exit_trade else None,
            entry_price = entry_price,
            exit_price = exit_price,
            remaining_quantity = round(remaining_quantity,5),
            quantity = quantity,
            profit = profit,
            profit_pct = profit_pct,
            max_drawdown = matched_trade_row.max_drawdown,
            max_runup = matched_trade_row.max_runup
        )
        self.df.loc[matched_trade_row_index] = updated_trade_row.to_list()
    
    def get_single_trade_history_row(self, index):
        trade_row_list = self.df.loc[index]
        trade_row = TradeRow(
            trade_direction = trade_row_list['trade_direction'],
            trade_type = trade_row_list['trade_type'],
            symbol = trade_row_list['symbol'],
            order_name = trade_row_list['order_name'],
            entry_time = trade_row_list['entry_time'],
            exit_time = trade_row_list['exit_time'],
            entry_price = trade_row_list['entry_price'],
            exit_price = trade_row_list['exit_price'],
            remaining_quantity = trade_row_list['remaining_quantity'],
            quantity = trade_row_list['quantity'],
            profit = trade_row_list['profit'],
            profit_pct = trade_row_list['profit_pct'],
            max_drawdown = trade_row_list['max_drawdown'],
            max_runup = trade_row_list['max_runup']
        )
        return trade_row
    
    def update_on_candle(self, market_data):
        index_list = self.get_open_position_index()
        for index in index_list:
            trade_row = self.get_single_trade_history_row(index)
            if trade_row.trade_direction == TradeDirection.Long:
                max_drawdown = min(trade_row.max_drawdown, trade_row.quantity * (market_data[trade_row.symbol].at[0,'low'] - trade_row.entry_price))
                max_runup = max(trade_row.max_runup, trade_row.quantity * (market_data[trade_row.symbol].at[0,'high'] - trade_row.entry_price))
            else:
                max_drawdown = min(trade_row.max_drawdown,  trade_row.quantity * (trade_row.entry_price - market_data[trade_row.symbol].at[0,'high']))
                max_runup = max(trade_row.max_runup,  trade_row.quantity * (trade_row.entry_price - market_data[trade_row.symbol].at[0,'low']))
            self.df.at[index, 'max_drawdown'] = max_drawdown
            self.df.at[index, 'max_runup'] = max_runup
        return self.df

    def get_most_traded_symbol(self):
        return self.df['symbol'].mode().at[0]