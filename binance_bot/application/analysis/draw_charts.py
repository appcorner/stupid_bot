import pandas as pd
import seaborn as sns # type: ignore
import matplotlib.pyplot as plt # type: ignore


class TradeActivitySingleSymbol:
    def __init__(self, trading_history: pd.DataFrame, trading_strategy, symbol: str, most_traded_symbol_market_data: pd.DataFrame):
        self.trading_history = trading_history
        self.trading_strategy = trading_strategy
        self.symbol = symbol
        self.most_traded_symbol_market_data = most_traded_symbol_market_data
        
    def prepare_data(self) -> pd.DataFrame:
        self.add_indicator()
        self.combine_with_trading_history()
        return self.df
    
    def display_chart(self):
        sns.set_theme(style="darkgrid")
        g = sns.relplot(x="time", y="close", kind="line", data=self.df)
        g.figure.autofmt_xdate()
        plt.show()
    
    def add_indicator(self):
        self.df = self.trading_strategy.add_indicators(self.most_traded_symbol_market_data)
        
    def combine_with_trading_history(self):
        trades_list = self.extract_trade_from_trading_history()
        self.df['long'] = self.attach_position_from_trading_history(trades_list, 'Long')
        self.df['short'] = self.attach_position_from_trading_history(trades_list, 'Short')
        self.df['buy'] = self.attach_action_from_trading_history(trades_list, 'Buy')
        self.df['sell'] = self.attach_action_from_trading_history(trades_list, 'Sell')
    
    def extract_trade_from_trading_history(self) -> list:
        filter_symbol = self.trading_history[self.trading_history['symbol'] == self.symbol]
        trade_list = []
        for index in filter_symbol.index:
            entry_time = filter_symbol.at[index,'entry_time']
            exit_time = filter_symbol.at[index,'exit_time']
            trade_direction = filter_symbol.at[index,'trade_direction']
            trade_list.append({'entry_time':entry_time,
                               'exit_time':exit_time,
                               'trade_direction':trade_direction})
        return trade_list
    
    def attach_position_from_trading_history(self, trades_list, trade_direction):
        result_column = False
        for trade in trades_list:
            if trade['trade_direction']==trade_direction:
                _result_column = (self.df['time'] >= trade['entry_time']) & (self.df['time'] <= trade['exit_time'] )
                result_column = result_column | _result_column
        return result_column
    
    def attach_action_from_trading_history(self, trades_list, side):
        result_column = False
        for trade in trades_list:
            if side == 'Buy':
                _result_column_long = (self.df['time'] == trade['entry_time']) & (trade['trade_direction'] == 'Long')
                _result_column_short = (self.df['time'] == trade['exit_time']) & (trade['trade_direction'] == 'Short')
                result_column = result_column | _result_column_long | _result_column_short
            elif side == 'Sell':
                _result_column_long = (self.df['time'] == trade['exit_time']) & (trade['trade_direction'] == 'Long')
                _result_column_short = (self.df['time'] == trade['entry_time']) & (trade['trade_direction'] == 'Short')
                result_column = result_column | _result_column_long | _result_column_short                
        return result_column
