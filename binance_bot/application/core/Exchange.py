import numpy as np
import pandas as pd
import binance
import datetime, application.core.BinanceModAddOn
from dataclasses import dataclass
from application.core import Event

pd.options.mode.chained_assignment = None
np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)


class Binance:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    async def start_connection(self):
        self.client = await binance.AsyncClient.create(self.api_key,self.api_secret)
        self.bm = binance.BinanceSocketManager(self.client, user_timeout = 120)

    def initial_settings(self, trading_strategy):
        self.watch_list = trading_strategy.watch_list
        self.parameters_on_data = trading_strategy.parameters_on_data
        self.parameters_on_risk = trading_strategy.parameters_on_risk
        self.market_data = MarketData(self.watch_list)
        self.orderbook_data = OrderBookData(self.watch_list)
        self.order_history = pd.DataFrame(columns = ['time', 'symbol', 'order_event', 'order_type', 'trade_direction', 'position_side', 'price', 'quantity','order_id','order_name','from_order'])
        self.liquidation_data = pd.DataFrame(columns = ['time', 'symbol', 'order_type','position_side', 'quantity', 'price', 'total_usd'])

    async def close_connection(self):
        await self.client.close_connection()
    
    async def request_change_leverage(self):
        for symbol in self.watch_list:
            try: await self.client.futures_change_leverage(symbol = symbol, leverage = self.parameters_on_risk.leverage)
            except binance.exceptions.BinanceAPIException as exception:
                print(exception)
        Event.log.notify(f'change leverage to {self.parameters_on_risk.leverage}')
        
    async def request_change_margin_mode(self):
        for symbol in self.watch_list:
            try: await self.client.futures_change_margin_type(symbol = symbol, marginType = self.parameters_on_risk.margin_mode)
            except binance.exceptions.BinanceAPIException as exception:
                if '4046' in f'{exception}': pass
        Event.log.notify(f'change margin type to {self.parameters_on_risk.margin_mode}')
    
    async def request_current_portfolio(self):
        res = await self.client.futures_account()
        Event.log.notify(f'request current portfolio data')
        portfolio_df = BinanceUtilities.request_current_portfolio(res, self.watch_list)
        await Event.on_portfolio_data_update.async_notify(portfolio_df)
        self.portfolio_df = portfolio_df
        return portfolio_df
    
    async def request_historical_candle_single(self,symbol):
        async for res in await self.client.futures_historical_klines_generator(symbol, self.parameters_on_data.candle_timeframe, self.parameters_on_data.historical_candle_lookback):
            candle = BinanceUtilities.request_historical_candle(symbol, res)
            self.market_data.update(candle, self.parameters_on_data.candle_max_length)
    
    async def request_historical_candle(self):
        for symbol in self.watch_list:
            await self.request_historical_candle_single(symbol)
        self.market_data.delete_recent_row()
        Event.log.notify(f'request current market data')
        await Event.on_market_data_update.async_notify(self.market_data.market_data_dict)
        return self.market_data.market_data_dict
    
    async def request_precision(self):
        res = await self.client.futures_exchange_info()
        Event.log.notify(f'request precision')
        self.precision_data = BinanceUtilities.request_precision(res, self.watch_list)
        return self.precision_data
    
    async def initialize_market_data_socket(self):
        ms = self.bm.futures_multiplex_socket([f'{symbol.lower()}@kline_{self.parameters_on_data.candle_timeframe}' for symbol in self.watch_list])
        Event.log.notify(f'initialize market data socket stream')
        async with ms as stream:
            while True:
                res = await stream.recv()
                if BinanceUtilities.market_data_socket_is_candle_closed(res):
                    candle = BinanceUtilities.market_data_socket(res)
                    self.market_data.update(candle, self.parameters_on_data.candle_max_length)
                    if self.market_data.is_candle_closed_for_every_symbol():
                        await Event.on_market_data_update.async_notify(self.market_data.market_data_dict)
                                
    async def initialize_orderbook_data_socket(self):
        ob = self.bm.futures_multiplex_socket([f'{symbol.lower()}@depth{self.parameters_on_data.orderbook_depth}' for symbol in self.watch_list])
        Event.log.notify(f'initialize orderbook data socket stream')
        async with ob as stream:
            while True:
                res = await stream.recv()
                orderbook = BinanceUtilities.orderbook_data_socket(res)
                self.orderbook_data.update(orderbook)
                await Event.on_orderbook_data_update.async_notify(self.orderbook_data.df)
                
    async def initialize_user_data_socket(self):
        us = self.bm.futures_user_socket()
        async with us as stream:
            while True:
                res = await stream.recv()
                if res['e'] == 'ORDER_TRADE_UPDATE':
                    self.order_history = BinanceUtilities.order_user_data_socket(res, self.order_history)
                    await Event.on_order_update.async_notify(self.order_history)
                elif res['e'] == 'ACCOUNT_UPDATE':
                    self.portfolio_df = BinanceUtilities.portfolio_update_user_data_socket(res, self.portfolio_df)
                    await Event.on_portfolio_data_update.async_notify(self.portfolio_df)
    
    async def initialize_liquidation_data_socket(self):
        lq = self.bm.futures_all_liquidation_orders()
        Event.log.notify(f'initialize liquidation data socket stream')
        await Event.on_liquidation_data_update.async_notify(self.liquidation_data)
        async with lq as stream:
            while True:
                res = await stream.recv()
                self.liquidation_data = BinanceUtilities.liquidation_data_socket(res, self.liquidation_data, self.parameters_on_data.liquidation_data_length, self.parameters_on_data.liquidation_data_criteria)
                await Event.on_liquidation_data_update.async_notify(self.liquidation_data)
    
    async def send_order(self, **kwargs):
        if kwargs.get('order_type') == 'MARKET':
            quantity = float(round(kwargs.get('quantity'),self.precision_data['quantity_precision'][kwargs.get('symbol')]))
            res = await self.client.futures_create_order(
                symbol = kwargs.get('symbol'),
                side = kwargs.get('trade_direction'),
                positionSide = kwargs.get('position_side'),
                type = 'MARKET',
                quantity = quantity
            )
        elif kwargs.get('order_type') == 'LIMIT':
            price = float(round(kwargs.get('price'),self.precision_data['price_precision'][kwargs.get('symbol')]))
            quantity = float(round(kwargs.get('quantity'),self.precision_data['quantity_precision'][kwargs.get('symbol')]))
            res = await self.client.futures_create_order(
                symbol = kwargs.get('symbol'),
                side = kwargs.get('trade_direction'),
                positionSide = kwargs.get('position_side'),
                type = 'LIMIT',
                quantity = quantity,
                price = price,
                timeInForce = 'GTC'
            )
        elif kwargs.get('order_type') == 'CANCEL':
            res = await self.client.futures_cancel_all_open_orders(symbol = kwargs.get('symbol'))
        self.order_history = BinanceUtilities.order_order_endpoint(res, self.order_history, kwargs.get('order_name'))
        await Event.on_order_update.async_notify(self.order_history)

@dataclass
class Candle:
    symbol: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketData:
    def __init__(self, watch_list):
        self.watch_list = watch_list
        self.market_data_dict = {}
        for symbol in self.watch_list:
            self.market_data_dict[symbol] = pd.DataFrame(columns = ['time', 'open', 'high', 'low', 'close', 'volume'])
        
    def update(self, candle, candle_max_length):
        self.market_data_dict[candle.symbol] = self.market_data_dict[candle.symbol][['time', 'open', 'high', 'low', 'close', 'volume']]
        self.market_data_dict[candle.symbol].loc[-1] = [candle.time, candle.open, candle.high, candle.low, candle.close, candle.volume]
        self.market_data_dict[candle.symbol].index += 1
        if len(self.market_data_dict[candle.symbol]) > candle_max_length:
            self.market_data_dict[candle.symbol] = self.market_data_dict[candle.symbol].drop([candle_max_length], axis = 0)

    def delete_recent_row(self):
        for symbol in self.watch_list:
            self.market_data_dict[symbol] = self.market_data_dict[symbol].drop([0], axis = 0)
            self.market_data_dict[symbol].index -= 1
    
    def is_candle_closed_for_every_symbol(self):
        time = self.market_data_dict[self.watch_list[0]]['time'][0]
        for symbol in self.watch_list:
            time_this_symbol = self.market_data_dict[symbol]['time'][0]
            if time_this_symbol != time:
                return False
        return True

@dataclass
class OrderBook:
    symbol : str
    bid_volume : list[float]
    bid : list[float]
    ask : list[float]
    ask_volume : list[float]
    
class OrderBookData:
    def __init__(self, watch_list):
        self.df = pd.DataFrame(columns=['symbol', 'bid_volume', 'bid', 'ask', 'ask_volume'],
                               index = watch_list)
        self.watch_list = watch_list
    
    def update(self, orderbook:OrderBook):
        self.df.loc[orderbook.symbol] = [orderbook.symbol, orderbook.bid_volume, orderbook.bid, orderbook.ask,orderbook.ask_volume]

class BinanceUtilities:
    def portfolio_row_creator(symbol, df, position_amount_column, entry_price_column):
        df['positionAmt_float'] = df[position_amount_column].apply(lambda x:float(x))
        df['entryPrice_float'] = df[entry_price_column].apply(lambda x:float(x))
        df['product_amt_entry'] = df['positionAmt_float']*df['entryPrice_float']
        long_inventory = df.loc[df['positionAmt_float'] > 0,'positionAmt_float'].sum()
        short_inventory = abs(df.loc[df['positionAmt_float'] < 0,'positionAmt_float'].sum())
        short_avg_cost = 0.0 if short_inventory == 0 else abs(df.loc[df['product_amt_entry'] < 0,'product_amt_entry'].sum()) / short_inventory
        long_avg_cost = 0.0 if long_inventory == 0 else df.loc[df['product_amt_entry'] > 0,'product_amt_entry'].sum() / long_inventory
        return [symbol, long_inventory, long_avg_cost, short_inventory, short_avg_cost]
    
    def request_current_portfolio(res, watch_list):
        res_df = pd.DataFrame(res['positions'])
        columns = ['symbol', 'long_inventory', 'long_entry', 'short_inventory', 'short_entry']
        portfolio_df = pd.DataFrame([[0,0,0,0,0]],columns = columns, index = watch_list)
        for symbol in watch_list:
            df = res_df[(res_df['symbol'].isin([symbol]))]
            portfolio_df.loc[symbol] = BinanceUtilities.portfolio_row_creator(symbol, df, 'positionAmt', 'entryPrice')
        return portfolio_df
    
    def request_historical_candle(symbol, res):
        time = datetime.datetime.fromtimestamp(res[0]/1000)
        candle = Candle(symbol, time,float(res[1]),float(res[2]),float(res[3]),float(res[4]),float(res[5]))
        return candle
    
    def request_precision(res, watch_list):
        df = pd.DataFrame(columns = ['symbol', 'price_precision', 'quantity_precision'], index = watch_list)
        res = res['symbols']
        for x in range(len(res)):
            if res[x]['symbol'] in watch_list:
                symbol = res[x]['symbol']
                price_precision = int(res[x]['pricePrecision'])
                quantity_precision = int(res[x]['quantityPrecision'])
                df.loc[symbol] = [symbol, price_precision, quantity_precision]
        return df
    
    def market_data_socket_is_candle_closed(res):
        return res['data']['k']['x']
    
    def market_data_socket(res):
        symbol = res['data']['s']
        time = datetime.datetime.fromtimestamp(res['data']['k']['t']/1000)
        open = float(res['data']['k']['o'])
        high = float(res['data']['k']['h'])
        low = float(res['data']['k']['l'])
        close = float(res['data']['k']['c'])
        volume = float(res['data']['k']['v'])
        return Candle(symbol,time,open,high,low,close,volume)
    
    def orderbook_data_socket(res):
        bid_df = pd.DataFrame(res['data']['b'])
        ask_df = pd.DataFrame(res['data']['a'])
        bid = [float(bid) for bid in bid_df[0]]
        ask = [float(ask) for ask in ask_df[0]]
        bid_volume = [float(bid_v) for bid_v in bid_df[1]]
        ask_volume = [float(ask_v) for ask_v in ask_df[1]]
        symbol = res['data']['s']
        return OrderBook(symbol, bid_volume, bid, ask, ask_volume)
    
    def order_order_endpoint(res, order_history, order_name):
        symbol = res["symbol"]
        time = datetime.datetime.fromtimestamp(res["updateTime"]/1000)
        order_event = res["status"]
        order_type = res["type"]
        trade_direction = res["side"]
        position_side = res["positionSide"]
        price = res["price"]
        quantity = res["origQty"]
        order_id = int(res["orderId"])
        order_name = order_name
        from_order = BinanceUtilities.match_order_name(order_history, 'symbol', symbol, 'order_name') if BinanceUtilities.is_exit_order(trade_direction,position_side) else ''
        order_history.loc[-1] = [time, symbol, order_event, order_type, trade_direction, position_side, price, quantity, order_id, order_name, from_order]
        order_history.index += 1
        return order_history
    
    def order_user_data_socket(res, order_history):
        symbol = res['o']['s']
        time = datetime.datetime.fromtimestamp(res['o']['T']/1000)
        order_event = res['o']['x']
        order_type = res['o']['ot']
        trade_direction = res['o']['S']
        position_side = res['o']['ps']
        price = float(res['o']['ap']) if float(res['o']['p']) == 0 else float(res['o']['p'])
        quantity = float(res['o']['l'])
        order_id = int(res['o']['i'])
        if order_event != 'NEW':
            order_name = BinanceUtilities.match_order_name(order_history, 'order_id', order_id, 'order_name')
            from_order = BinanceUtilities.match_order_name(order_history, 'symbol', symbol, 'from_order') if BinanceUtilities.is_exit_order(trade_direction,position_side) else ''
            order_history.loc[-1] = [time, symbol, order_event, order_type, trade_direction, position_side, price, quantity, order_id, order_name, from_order]
            order_history.index += 1
        return order_history
    
    def match_order_name(order_history, column, column_value, call_for):
        row = order_history.loc[order_history[column] == column_value]
        try: return row[call_for].iloc[-1]
        except IndexError: 
            print(row)
            raise IndexError ('No previous entry order available: Exit order should not be your first order')
    
    def is_exit_order(trade_direction, position_side):
        is_exit_long_order = (trade_direction=='SELL') & (position_side=='LONG')
        is_exit_short_order = (trade_direction=='BUY') & (position_side=='SHORT')
        return is_exit_long_order or is_exit_short_order
    
    def portfolio_update_user_data_socket(res, portfolio_df):
        df = pd.DataFrame(res['a']['P'])
        symbol = df['s'][0]
        portfolio_df.loc[symbol] = BinanceUtilities.portfolio_row_creator(symbol, df, 'pa','ep')
        return portfolio_df
    
    def liquidation_data_socket(res, liquidation_data, max_length, criteria):
        order_res = res['data']['o']
        time = datetime.datetime.fromtimestamp(order_res['T']/1000)
        symbol = order_res['s']
        order_type = order_res['o']
        side = 1 if order_res['S'] == 'BUY' else -1
        position_side = order_res['S']
        quantity = float(order_res['q']) * side
        price = float(order_res['ap'])
        total_usd = price*quantity
        if abs(total_usd)>criteria:
            liquidation_data.loc[-1] = [time, symbol, order_type,position_side, quantity, price, abs(total_usd)]
            liquidation_data.index += 1
            if len(liquidation_data)>max_length:
                liquidation_data = liquidation_data.drop([max_length], axis = 0)
        return liquidation_data