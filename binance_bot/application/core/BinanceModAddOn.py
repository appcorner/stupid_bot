from binance import BinanceSocketManager
from binance.enums import FuturesType

def futures_all_liquidation_orders(self, futures_type: FuturesType = FuturesType.USD_M):
    return self._get_futures_socket('!forceOrder@arr', futures_type=futures_type)

BinanceSocketManager.futures_all_liquidation_orders = futures_all_liquidation_orders



def futures_liquidation_orders(self, symbol: str, futures_type: FuturesType = FuturesType.USD_M):
    return self._get_futures_socket(symbol.lower() + '@forceOrder', futures_type=futures_type)

BinanceSocketManager.futures_liquidation_orders = futures_liquidation_orders
