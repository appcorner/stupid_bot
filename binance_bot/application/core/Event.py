class Event:
    def __init__(self):
        self.listeners = []

    def __iadd__(self, listener):
        """Shortcut for using += to add a listener."""
        self.listeners.append(listener)
        return self

    def __isub__(self, listener):
        """Shortcut for using -= to add a listener."""
        self.listeners.remove(listener)
        return self

    def notify(self, *args, **kwargs):
        for listener in self.listeners:
            listener(*args, **kwargs)
            
    async def async_notify(self, *args, **kwargs):
        for listener in self.listeners:
            await listener(*args, **kwargs)
            
'''Event Creator : App'''
on_second = Event()
log  = Event()
on_app_shutdown = Event()
'''Event Creator : TradingStrategy'''
on_send_order = Event()
'''Event Creator : Exchange'''
on_market_data_update = Event()
on_orderbook_data_update = Event()
on_portfolio_data_update = Event()
on_order_update = Event()
on_liquidation_data_update = Event()