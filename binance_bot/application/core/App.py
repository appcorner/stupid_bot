import asyncio
from application.core import Log
from application.core import Event

class App:
    def __init__(self, name, exchange, trading_strategy, record_trade):
        self.name = name
        self.exchange = exchange
        self.trading_strategy = trading_strategy
        self.record_trade = record_trade
        
    async def start(self):
        await self.exchange.start_connection()
        self.portfolio_data, self.trade_history = self.record_trade.create_tables()
    
    async def quit(self):
        await self.exchange.close_connection()
        print(self.record_trade.finalize_result())
    
    async def run(self):
        await self.on_initialize()
        await asyncio.gather(
            self.on_second(),
            self.exchange.initialize_market_data_socket(),
            self.exchange.initialize_orderbook_data_socket(),
            self.exchange.initialize_user_data_socket(),
            self.exchange.initialize_liquidation_data_socket()
        )

    async def on_initialize(self):
        Log.setup_logger(self.name)
        Event.log += Log.logger_main_handler
        Log.setup_activity_logger(f'{self.name}_activity')
        Event.on_order_update += Log.logger_activity_handler
        self.exchange.initial_settings(self.trading_strategy)
        
        Event.log.notify('-------Start-------')
        
        Event.on_market_data_update += self.on_market_data_update_activity_first
        Event.on_orderbook_data_update += self.on_orderbook_data_update_activity
        Event.on_order_update += self.on_order_update_activity
        Event.on_liquidation_data_update += self.on_liquidation_data_update_activity
        Event.on_app_shutdown += self.on_app_shutdown_activity
        Event.on_send_order += self.exchange.send_order
        
        await self.exchange.request_change_leverage()
        await self.exchange.request_change_margin_mode()
        await self.exchange.request_historical_candle()
        await self.exchange.request_current_portfolio()
        await self.exchange.request_precision()

    async def on_second(self):
        Event.on_second += self.on_second_activity
        while True:
            await asyncio.sleep(1)
            await Event.on_second.async_notify()
    
    async def on_second_activity(self):
        if hasattr(self, 'orderbook_data'): 
            await self.trading_strategy.on_second(self.market_data, self.orderbook_data, self.portfolio_data, self.liquidation_data)
    
    async def on_market_data_update_activity_first(self, market_data):
        self.market_data = market_data
        Event.on_market_data_update -= self.on_market_data_update_activity_first
        Event.on_market_data_update += self.on_market_data_update_activity
    
    async def on_market_data_update_activity(self, market_data):
        self.market_data = market_data
        self.add_indicators()
        self.order_history = self.exchange.order_history
        await self.trading_strategy.on_candle_closed(self.market_data, 
                                                     self.orderbook_data,
                                                     self.portfolio_data, 
                                                     self.liquidation_data, 
                                                     self.order_history,
                                                     self.trade_history)
        self.portfolio_data, self.trade_history = self.record_trade.update_on_candle(self.market_data)
        
    async def on_orderbook_data_update_activity(self, orderbook_data):
        self.orderbook_data = orderbook_data
        
    async def on_order_update_activity(self, order_history):
        self.order_history = order_history
        await self.trading_strategy.on_order_updated(self.order_history)
        self.portfolio_data, self.trade_history = self.record_trade.record_order(order_history)
        self.record_trade.export_result()
        
    async def on_liquidation_data_update_activity(self, liquidation_data):
        self.liquidation_data = liquidation_data
        
    def add_indicators(self):
        for symbol in self.trading_strategy.watch_list:
            df = self.market_data[symbol]
            self.market_data[symbol] = self.trading_strategy.add_indicators(df)
            
    async def on_app_shutdown_activity(self):
        await self.trading_strategy.on_app_shutdown(self.market_data, self.orderbook_data,self.portfolio_data, self.liquidation_data)
        Event.log.notify('-------Shut down-------')