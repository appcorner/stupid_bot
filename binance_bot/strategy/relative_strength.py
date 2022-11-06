import asyncio
import pandas as pd
from dataclasses import dataclass
from application.core.PerformanceReader import PerformanceData
from application.core.TraderAction import LongEntry_MarketOrder, ShortEntry_MarketOrder, Close_All_Position

# Watch_List = ['BTCUSDT','ETHUSDT','BCHUSDT','XRPUSDT','EOSUSDT','LTCUSDT','TRXUSDT','ETCUSDT','LINKUSDT','XLMUSDT','ADAUSDT','XMRUSDT','DASHUSDT','ZECUSDT','XTZUSDT','BNBUSDT','ATOMUSDT','ONTUSDT','IOTAUSDT','BATUSDT','VETUSDT','NEOUSDT','QTUMUSDT','IOSTUSDT','THETAUSDT','ALGOUSDT','ZILUSDT','KNCUSDT','ZRXUSDT','COMPUSDT','OMGUSDT','DOGEUSDT','SXPUSDT','KAVAUSDT','BANDUSDT','RLCUSDT','WAVESUSDT','MKRUSDT','SNXUSDT','DOTUSDT','DEFIUSDT','YFIUSDT','BALUSDT','CRVUSDT','TRBUSDT','YFIIUSDT','RUNEUSDT','SUSHIUSDT','SRMUSDT','BZRXUSDT','EGLDUSDT','SOLUSDT','ICXUSDT','STORJUSDT','BLZUSDT','UNIUSDT','AVAXUSDT','FTMUSDT','HNTUSDT','ENJUSDT','FLMUSDT','TOMOUSDT','RENUSDT','KSMUSDT','NEARUSDT','AAVEUSDT','FILUSDT','RSRUSDT','LRCUSDT','MATICUSDT','OCEANUSDT','CVCUSDT','BELUSDT','CTKUSDT','AXSUSDT','ALPHAUSDT','ZENUSDT','SKLUSDT','GRTUSDT','1INCHUSDT','BTCBUSD','AKROUSDT','CHZUSDT','SANDUSDT','ANKRUSDT','LUNAUSDT','BTSUSDT','LITUSDT','UNFIUSDT','DODOUSDT','REEFUSDT','RVNUSDT','SFPUSDT','XEMUSDT','BTCSTUSDT','COTIUSDT','CHRUSDT','MANAUSDT','ALICEUSDT','HBARUSDT','ONEUSDT','LINAUSDT','STMXUSDT','DENTUSDT','CELRUSDT','HOTUSDT','MTLUSDT','OGNUSDT','BTTUSDT','NKNUSDT','SCUSDT','DGBUSDT','1000SHIBUSDT','ICPUSDT','BAKEUSDT','GTCUSDT','ETHBUSD','BTCDOMUSDT','KEEPUSDT','TLMUSDT','BNBBUSD','ADABUSD','XRPBUSD','IOTXUSDT','DOGEBUSD','AUDIOUSDT','RAYUSDT','C98USDT','MASKUSDT','ATAUSDT','SOLBUSD','FTTBUSD','DYDXUSDT','1000XECUSDT','GALAUSDT','CELOUSDT','ARUSDT','KLAYUSDT','ARPAUSDT','NUUSDT','CTSIUSDT','LPTUSDT']
Watch_List = ['GALAUSDT','TOMOUSDT','LRCUSDT','ALGOUSDT','1000SHIBUSDT','ONEUSDT','CRVUSDT','OGNUSDT','RSRUSDT','ENJUSDT','MANAUSDT','CELRUSDT','CTKUSDT','DODOUSDT','ALPHAUSDT','CTSIUSDT','ATAUSDT','IOSTUSDT','AUDIOUSDT','CHZUSDT','HOTUSDT','ARPAUSDT','SFPUSDT','DGBUSDT','FLMUSDT','REEFUSDT','BZRXUSDT','AKROUSDT','LITUSDT','BAKEUSDT','SKLUSDT','BLZUSDT','FTMUSDT','BELUSDT','COTIUSDT','HBARUSDT','GRTUSDT','RENUSDT','KAVAUSDT','SRMUSDT','CELOUSDT','DENTUSDT','BATUSDT','OCEANUSDT','SXPUSDT','ZILUSDT','VETUSDT','XTZUSDT','LINAUSDT','KEEPUSDT','TRXUSDT','ONTUSDT','NKNUSDT','KNCUSDT','XEMUSDT','BTTUSDT','MTLUSDT','ZRXUSDT','IOTAUSDT','MATICUSDT','SANDUSDT','1000XECUSDT','DOGEUSDT','BTSUSDT','C98USDT','TLMUSDT','XLMUSDT','EOSUSDT','STMXUSDT','CVCUSDT','XRPUSDT','1INCHUSDT','RVNUSDT','ICXUSDT','ADAUSDT','NUUSDT','SCUSDT','RLCUSDT','KLAYUSDT','IOTXUSDT','ANKRUSDT','STORJUSDT','CHRUSDT']
# Watch_List = ['XRPUSDT','GALAUSDT','TOMOUSDT','LRCUSDT','ALGOUSDT','1000SHIBUSDT']


@dataclass
class ParametersOnRisk:
    leverage : int = 1
    margin_mode : str = 'CROSSED'
    currency : str = 'USDT'
    
@dataclass
class ParametersOnData:
    candle_max_length : int = 120
    candle_timeframe : str = '1m'
    historical_candle_lookback : str = '2 hr ago UTC'
    orderbook_depth: int = 5
    liquidation_data_length: int = 5
    liquidation_data_criteria: float = 0.0

class TradingStrategy:
    def __init__(self):
        self.watch_list = Watch_List
        self.parameters_on_data = ParametersOnData()
        self.parameters_on_risk = ParametersOnRisk()
        self.usdt_per_trade = 7.0
        self.strength_lookback = 2
        self.symbols_to_trade_on_each_side = 2
        self.count = 0
        self.relative_strength = pd.DataFrame([[0]], columns = ['a'],  index=self.watch_list)
        self.is_momentum_time = True
    
    async def on_second(self, market_data, orderbook_data, portfolio_data, liquidation_data):
        # print(orderbook_data)
        pass
    
    async def on_candle_closed(self, market_data, orderbook_data, portfolio_data, liquidation_data, order_history, trade_history):
        await asyncio.sleep(2)
        
        for symbol in self.watch_list:
            self.relative_strength.loc[symbol] = float(market_data[symbol]['close'][0] / market_data[symbol]['close'][self.strength_lookback])
        
        if self.count == 0:
            try: await Close_All_Position(portfolio_data)
            except KeyError: pass
            await self.check_last_performance(order_history)
            if self.is_momentum_time: await self.momentum_entry(market_data)
            else: await self.mean_reversion_entry(market_data)
            self.count += 1
        elif self.count > self.strength_lookback:
            self.count = 0
        else:
            self.count += 1
        
        pass

    async def on_order_updated(self, order_history):
        pass

    async def on_app_shutdown(self, market_data, orderbook_data, portfolio_data, liquidation_data):
        await Close_All_Position(portfolio_data)
        pass
    
    def add_indicators(self, df):
        return df
             
    async def momentum_entry(self, market_data):
        print('Enter Momentum Positions')
        df = self.relative_strength
        highest_symbol = df.nlargest(self.symbols_to_trade_on_each_side, 'a').index
        lowest_symbol  = df.nsmallest(self.symbols_to_trade_on_each_side, 'a').index
        for symbol, index in zip(highest_symbol,range(0,self.symbols_to_trade_on_each_side )):
            await LongEntry_MarketOrder(symbol,self.usdt_per_trade/market_data[symbol]['close'][0], order_name=f'Momentum_LONG_{index}')
        for symbol, index in zip(lowest_symbol,range(0,self.symbols_to_trade_on_each_side )):
            await ShortEntry_MarketOrder(symbol,self.usdt_per_trade/market_data[symbol]['close'][0], order_name=f'Momentum_SHORT_{index}')
    
    async def mean_reversion_entry(self, market_data):
        print('Enter MeanReversion Positions')
        df = self.relative_strength
        highest_symbol = df.nlargest(self.symbols_to_trade_on_each_side, 'a').index
        lowest_symbol  = df.nsmallest(self.symbols_to_trade_on_each_side, 'a').index
        for symbol, index in zip(highest_symbol,range(0,self.symbols_to_trade_on_each_side )):
            await ShortEntry_MarketOrder(symbol,self.usdt_per_trade/market_data[symbol]['close'][0], order_name=f'Mean_Reversion_SHORT_{index}')
        for symbol, index in zip(lowest_symbol,range(0,self.symbols_to_trade_on_each_side )):
            await LongEntry_MarketOrder(symbol,self.usdt_per_trade/market_data[symbol]['close'][0], order_name=f'Mean_Reversion_LONG_{index}')

    async def check_last_performance(self,order_history):
        await asyncio.sleep(1)
        if len(order_history)!=0:
            perf = PerformanceData(
                order_history=order_history,
                prev_order_history=self.prev_order_history,
                tracked_order_name=''
            )
            perf.run()
            if perf.metrics.net_realized_pnl < 0: self.is_momentum_time=not(self.is_momentum_time)
            # perf.metrics.display()
        self.prev_order_history=order_history.copy()
        await asyncio.sleep(1)

'''market_data'''
# {
# 'BTCUSDT':                   
#                   time     open     high      low    close    volume        
# 59 2021-11-17 13:43:00  4175.01  4176.62  4172.16  4172.16   245.754
# 58 2021-11-17 13:44:00  4172.16  4175.07  4170.11  4174.71   580.690
# ... 
# 1  2021-11-17 14:41:00  4183.58  4194.67  4182.16  4190.71  4110.064
# 0  2021-11-17 14:42:00  4190.91  4199.11  4186.68  4197.39  3209.356
# ,
# 'ETHUSDT':                   
#                   time     open     high      low    close    volume        
# 59 2021-11-17 13:43:00  4175.01  4176.62  4172.16  4172.16   245.754
# 58 2021-11-17 13:44:00  4172.16  4175.07  4170.11  4174.71   580.690
# ... 
# 1  2021-11-17 14:41:00  4183.58  4194.67  4182.16  4190.71  4110.064
# 0  2021-11-17 14:42:00  4190.91  4199.11  4186.68  4197.39  3209.356
# }

'''market_data['BTC']  (After add ATR indicator)'''
#                   time      open      high       low     close   volume        atr
# 4  2021-11-18 15:18:00  59703.89  59716.03  59661.89  59690.15   86.536  72.077347
# 3  2021-11-18 15:19:00  59689.72  59714.99  59676.81  59692.08   43.722  69.656108
# 2  2021-11-18 15:20:00  59692.07  59805.22  59683.94  59805.09  285.338  73.343529
# 1  2021-11-18 15:21:00  59805.09  59820.00  59755.00  59764.44  151.254  72.747562
# 0  2021-11-18 15:22:00  59764.45  59783.80  59746.24  59783.79   54.308  70.234165


'''portfolio_data'''
#           symbol long_inventory short_inventory 
# BTCUSDT  BTCUSDT            0.0             0.0 
# ETHUSDT  ETHUSDT            0.0             0.0 
# XRPUSDT  XRPUSDT            5.4             0.0 
# GALAUSDT GALAUSDT           0              -5.7  

'''orderbook_data'''
#           symbol                          bid_volume  ...                                              ask                           ask_volume
# BTCUSDT  BTCUSDT  [0.608, 0.224, 0.05, 0.001, 0.002]  ...  [59675.38, 59675.4, 59676.6, 59676.7, 59678.46]  [0.748, 0.062, 0.004, 0.001, 0.048]
# ETHUSDT  ETHUSDT   [4.708, 0.006, 3.002, 2.437, 2.0]  ...     [4177.77, 4177.78, 4177.95, 4178.0, 4178.01]   [10.487, 0.2, 3.985, 0.191, 0.362]

'''liquidation_data'''
#                      time     symbol order_type position_side  quantity   price  total_usd
# 4 2021-11-18 13:24:55.887  AUDIOUSDT      LIMIT          SELL     -40.0   2.860   114.4000
# 3 2021-11-18 13:25:04.219    LPTUSDT      LIMIT          SELL      -5.0  53.470   267.3500
# 2 2021-11-18 13:25:09.679    LPTUSDT      LIMIT          SELL      -0.4  53.453    21.3812
# 1 2021-11-18 13:25:12.143    LPTUSDT      LIMIT          SELL      -2.1  53.407   112.1547
# 0 2021-11-18 13:25:14.661    LPTUSDT      LIMIT          SELL      -0.5  53.398    26.6990

'''order_history'''
#                      time   symbol order_event order_type trade_direction position_side   price  quantity
# 5 2021-11-18 13:33:31.660  XRPUSDT         NEW      LIMIT            SELL         SHORT  1.1331       5.4
# 4 2021-11-18 13:33:36.796  XRPUSDT    CANCELED      LIMIT            SELL         SHORT  1.1331       5.4
# 3 2021-11-18 13:33:41.903  XRPUSDT         NEW     MARKET             BUY          LONG  0.0000       5.4
# 2 2021-11-18 13:33:41.903  XRPUSDT       TRADE     MARKET             BUY          LONG  1.1114       5.4
# 1 2021-11-18 13:33:47.017  XRPUSDT         NEW     MARKET            SELL          LONG  0.0000       5.4
# 0 2021-11-18 13:33:47.017  XRPUSDT       TRADE     MARKET            SELL          LONG  1.1113       5.4