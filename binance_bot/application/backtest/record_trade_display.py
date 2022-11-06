import datetime
import pandas as pd
import os
term_size = os.get_terminal_size()


class CalculateTradeStatistics:
    def __init__(self, trade_history:pd.DataFrame):
        self.df = trade_history.copy().reset_index(drop = True)
        self.df['holding_period'] = pd.to_datetime(self.df['exit_time']) - pd.to_datetime(self.df['entry_time'])

    def perform_calculation(self):
        self.calculate_profit()
        self.calculate_maxmin()
        self.count_trades()
        self.calculate_avg_stats()
        self.calculate_holding_period()
        self.calculate_ratio_stats()
        
    def calculate_profit(self):
        self.net_profit = self.df['profit'].sum()
        self.gross_profit = self.df[self.df['profit']>0]['profit'].sum()
        self.gross_loss = self.df[self.df['profit']<0]['profit'].sum()
        
    def calculate_maxmin(self):
        self.max_win = self.df[self.df['profit']>0]['profit'].max()
        self.max_win_pct = self.df[self.df['profit_pct']>0]['profit_pct'].max()
        self.max_loss = self.df[self.df['profit']<0]['profit'].min()
        self.max_loss_pct = self.df[self.df['profit_pct']<0]['profit_pct'].min()
        self.max_drawdown_worst = self.df['max_drawdown'].min()
        self.max_drawdown_average = self.df['max_drawdown'].mean()
        self.max_runup_best = self.df['max_runup'].max()
        self.max_runup_average = self.df['max_runup'].mean()
        
    def count_trades(self):
        self.total_trades = len(self.df['profit'])
        self.total_winning_trades = len(self.df[self.df['profit']>0])
        self.total_losing_trades = len(self.df[self.df['profit']<0])
        self.pct_protitable_trades = self.total_winning_trades / self.total_trades
        
    def calculate_avg_stats(self):
        self.avg_trade = self.df['profit'].mean()
        self.avg_winning_trade = self.df[self.df['profit']>0]['profit'].mean()
        self.avg_losing_trade = self.df[self.df['profit']<0]['profit'].mean()
        self.avg_trade_pct = self.df['profit_pct'].mean()
        self.avg_winning_trade_pct = self.df[self.df['profit_pct']>0]['profit_pct'].mean()
        self.avg_losing_trade_pct = self.df[self.df['profit_pct']<0]['profit_pct'].mean()
        
    def calculate_holding_period(self):
        self.max_holding_period = self.df['holding_period'].max()
        self.avg_holding_period = self.df['holding_period'].mean()
        self.avg_holding_period_winning = self.df[self.df['profit']>0]['holding_period'].mean()
        self.avg_holding_period_losing = self.df[self.df['profit']>0]['holding_period'].mean()
        self.total_trading_period = pd.to_datetime(self.df.at[len(self.df)-1,'exit_time']) - pd.to_datetime(self.df.at[0,'entry_time'])
        
    def calculate_ratio_stats(self):
        self.sharpe_ratio = self.df['profit_pct'].mean() / self.df['profit_pct'].std() * ((datetime.timedelta(days=252)/self.total_trading_period)**0.5)
        self.profit_factor = self.gross_profit / abs(self.gross_loss)
        # self.sortino_ratio # TODO sortino_ratio
    
    def result(self):
        text = '\n'
        text += '_' * term_size.columns
        for attribute, value in self.__dict__.items():
            if type(value) != pd.DataFrame:
                text += (f'\n{attribute:<30s}: {value}')
        text += '\n'+'_' * term_size.columns
        return text