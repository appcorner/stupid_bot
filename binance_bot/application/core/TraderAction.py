from application.core import Event

async def LongEntry_LimitOrder(symbol, price, quantity, order_name=''):
    await Event.on_send_order.async_notify(order_type="LIMIT", position_side="LONG", trade_direction="BUY",symbol=symbol, price=price, quantity=quantity, order_name=order_name)

async def ShortEntry_LimitOrder(symbol, price, quantity, order_name=''):
    await Event.on_send_order.async_notify(order_type="LIMIT", position_side="SHORT", trade_direction="SELL",symbol=symbol, price=price, quantity=quantity, order_name=order_name)
    
async def LongExit_LimitOrder(symbol, price, quantity, order_name=''):
    await Event.on_send_order.async_notify(order_type="LIMIT", position_side="LONG", trade_direction="SELL",symbol=symbol, price=price, quantity=quantity, order_name=order_name)

async def ShortExit_LimitOrder(symbol, price, quantity, order_name=''):
    await Event.on_send_order.async_notify(order_type="LIMIT", position_side="SHORT", trade_direction="BUY",symbol=symbol, price=price, quantity=quantity, order_name=order_name)
    
async def LongEntry_MarketOrder(symbol, quantity, order_name=''):
    await Event.on_send_order.async_notify(order_type="MARKET", position_side="LONG", trade_direction="BUY",symbol=symbol, quantity=quantity, order_name=order_name)

async def ShortEntry_MarketOrder(symbol, quantity, order_name=''):
    await Event.on_send_order.async_notify(order_type="MARKET", position_side="SHORT", trade_direction="SELL",symbol=symbol, quantity=quantity, order_name=order_name)
    
async def LongExit_MarketOrder(symbol, quantity, order_name=''):
    await Event.on_send_order.async_notify(order_type="MARKET", position_side="LONG", trade_direction="SELL",symbol=symbol, quantity=quantity, order_name=order_name)

async def ShortExit_MarketOrder(symbol, quantity, order_name=''):
    await Event.on_send_order.async_notify(order_type="MARKET", position_side="SHORT", trade_direction="BUY",symbol=symbol, quantity=quantity, order_name=order_name)
    
async def Cancel_AllOpenOrders(symbol, order_name=''):
    await Event.on_send_order.async_notify(order_type="CANCEL", symbol=symbol, order_name=order_name)
    
async def Close_All_Position(portfolio_data):
    long_symbol = portfolio_data[portfolio_data['long_inventory']>0].index
    short_symbol = portfolio_data[portfolio_data['short_inventory']>0].index
    for symbol in long_symbol:
        if portfolio_data['long_inventory'][symbol] == 0: break
        await LongExit_MarketOrder(symbol, portfolio_data['long_inventory'][symbol])
    for symbol in short_symbol:
        if portfolio_data['short_inventory'][symbol] == 0: break
        await ShortExit_MarketOrder(symbol, portfolio_data['short_inventory'][symbol])