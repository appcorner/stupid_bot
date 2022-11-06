from dataclasses import dataclass
from application.core.Exchange import Binance, BinanceUtilities
from application.backtest.database_market_data import CSVMarketData
from application.core import Event


# Watch_List = ['BTCUSDT','ETHUSDT','BCHUSDT','XRPUSDT','EOSUSDT','LTCUSDT','TRXUSDT','ETCUSDT','LINKUSDT','XLMUSDT','ADAUSDT','XMRUSDT','DASHUSDT','ZECUSDT','XTZUSDT','BNBUSDT','ATOMUSDT','ONTUSDT','IOTAUSDT','BATUSDT','VETUSDT','NEOUSDT','QTUMUSDT','IOSTUSDT','THETAUSDT','ALGOUSDT','ZILUSDT','KNCUSDT','ZRXUSDT','COMPUSDT','OMGUSDT','DOGEUSDT','SXPUSDT','KAVAUSDT','BANDUSDT','RLCUSDT','WAVESUSDT','MKRUSDT','SNXUSDT','DOTUSDT','DEFIUSDT','YFIUSDT','BALUSDT','CRVUSDT','TRBUSDT','YFIIUSDT','RUNEUSDT','SUSHIUSDT','SRMUSDT','BZRXUSDT','EGLDUSDT','SOLUSDT','ICXUSDT','STORJUSDT','BLZUSDT','UNIUSDT','AVAXUSDT','FTMUSDT','HNTUSDT','ENJUSDT','FLMUSDT','TOMOUSDT','RENUSDT','KSMUSDT','NEARUSDT','AAVEUSDT','FILUSDT','RSRUSDT','LRCUSDT','MATICUSDT','OCEANUSDT','CVCUSDT','BELUSDT','CTKUSDT','AXSUSDT','ALPHAUSDT','ZENUSDT','SKLUSDT','GRTUSDT','1INCHUSDT','BTCBUSD','AKROUSDT','CHZUSDT','SANDUSDT','ANKRUSDT','LUNAUSDT','BTSUSDT','LITUSDT','UNFIUSDT','DODOUSDT','REEFUSDT','RVNUSDT','SFPUSDT','XEMUSDT','BTCSTUSDT','COTIUSDT','CHRUSDT','MANAUSDT','ALICEUSDT','HBARUSDT','ONEUSDT','LINAUSDT','STMXUSDT','DENTUSDT','CELRUSDT','HOTUSDT','MTLUSDT','OGNUSDT','BTTUSDT','NKNUSDT','SCUSDT','DGBUSDT','1000SHIBUSDT','ICPUSDT','BAKEUSDT','GTCUSDT','ETHBUSD','BTCDOMUSDT','KEEPUSDT','TLMUSDT','BNBBUSD','ADABUSD','XRPBUSD','IOTXUSDT','DOGEBUSD','AUDIOUSDT','RAYUSDT','C98USDT','MASKUSDT','ATAUSDT','SOLBUSD','FTTBUSD','DYDXUSDT','1000XECUSDT','GALAUSDT','CELOUSDT','ARUSDT','KLAYUSDT','ARPAUSDT','NUUSDT','CTSIUSDT','LPTUSDT']
Watch_List = [
    "GALAUSDT",
    "TOMOUSDT",
    "LRCUSDT",
    "ALGOUSDT",
    "1000SHIBUSDT",
    "ONEUSDT",
    "CRVUSDT",
    "OGNUSDT",
    "RSRUSDT",
    "ENJUSDT",
    "MANAUSDT",
    "CELRUSDT",
    "CTKUSDT",
    "DODOUSDT",
    "ALPHAUSDT",
    "CTSIUSDT",
    "ATAUSDT",
    "IOSTUSDT",
    "AUDIOUSDT",
    "CHZUSDT",
    "HOTUSDT",
    "ARPAUSDT",
    "SFPUSDT",
    "DGBUSDT",
    "FLMUSDT",
    "REEFUSDT",
    "AKROUSDT",
    "LITUSDT",
    "BAKEUSDT",
    "SKLUSDT",
    "BLZUSDT",
    "FTMUSDT",
    "BELUSDT",
    "COTIUSDT",
    "HBARUSDT",
    "GRTUSDT",
    "RENUSDT",
    "KAVAUSDT",
    "SRMUSDT",
    "CELOUSDT",
    "DENTUSDT",
    "BATUSDT",
    "OCEANUSDT",
    "SXPUSDT",
    "ZILUSDT",
    "VETUSDT",
    "XTZUSDT",
    "LINAUSDT",
    "KEEPUSDT",
    "TRXUSDT",
    "ONTUSDT",
    "NKNUSDT",
    "KNCUSDT",
    "XEMUSDT",
    "BTTUSDT",
    "MTLUSDT",
    "ZRXUSDT",
    "IOTAUSDT",
    "MATICUSDT",
    "SANDUSDT",
    "1000XECUSDT",
    "DOGEUSDT",
    "BTSUSDT",
    "C98USDT",
    "TLMUSDT",
    "XLMUSDT",
    "EOSUSDT",
    "STMXUSDT",
    "CVCUSDT",
    "XRPUSDT",
    "1INCHUSDT",
    "RVNUSDT",
    "ICXUSDT",
    "ADAUSDT",
    "NUUSDT",
    "SCUSDT",
    "RLCUSDT",
    "KLAYUSDT",
    "IOTXUSDT",
    "ANKRUSDT",
    "STORJUSDT",
    "CHRUSDT",
]
# Watch_List = ['XRPUSDT','GALAUSDT','TOMOUSDT','LRCUSDT','ALGOUSDT','1000SHIBUSDT']

DATABASE_NAME = ["data_for_test", "25_DEC_2021"]
CANDLE_TIMEFRAME = "5m"
CANDLE_MAX_RECORD = 1500
FROM_DATE = "25 Dec, 2021"
TO_DATE = "26 Dec, 2021"

database = CSVMarketData(DATABASE_NAME)
database.clear_all_csv_files()


async def request_historical_candle(self):
    for symbol, i in zip(self.watch_list, range(0, len(self.watch_list))):
        await self.request_historical_candle_single(symbol)
        database.create_csv(symbol, self.market_data.market_data_dict[symbol])
        print(f"{symbol}\t: success {i+1}/{len(self.watch_list)}")
    self.market_data.delete_recent_row()
    Event.log.notify(f"request current market data")
    await Event.on_market_data_update.async_notify(self.market_data.market_data_dict)
    return self.market_data.market_data_dict


async def request_historical_candle_single(self, symbol):
    async for res in await self.client.futures_historical_klines_generator(
        symbol, self.parameters_on_data.candle_timeframe, FROM_DATE, TO_DATE
    ):
        candle = BinanceUtilities.request_historical_candle(symbol, res)
        self.market_data.update(candle, self.parameters_on_data.candle_max_length)


Binance.request_historical_candle = request_historical_candle
Binance.request_historical_candle_single = request_historical_candle_single


@dataclass
class ParametersOnRisk:
    leverage: int = 1
    margin_mode: str = "CROSSED"
    currency: str = "USDT"


@dataclass
class ParametersOnData:
    candle_max_length: int = CANDLE_MAX_RECORD
    candle_timeframe: str = CANDLE_TIMEFRAME
    historical_candle_lookback: str = "4 hr ago UTC"
    orderbook_depth: int = 5
    liquidation_data_length: int = 5
    liquidation_data_criteria: float = 0.0


class TradingStrategy:
    def __init__(self):
        self.watch_list = Watch_List
        self.parameters_on_data = ParametersOnData()
        self.parameters_on_risk = ParametersOnRisk()

    async def on_second(
        self, market_data, orderbook_data, portfolio_data, liquidation_data
    ):
        print("Finished!")

    async def on_candle_closed(
        self,
        market_data,
        orderbook_data,
        portfolio_data,
        liquidation_data,
        order_history,
        trade_history,
    ):
        pass

    async def on_portfolio_updated(self, portfolio_data):
        pass

    async def on_order_updated(self, order_history):
        pass

    async def on_app_shutdown(
        self, market_data, orderbook_data, portfolio_data, liquidation_data
    ):
        pass

    def add_indicators(self, df):
        return df
