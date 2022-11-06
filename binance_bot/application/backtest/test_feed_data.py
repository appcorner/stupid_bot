from unittest import TestCase
from unittest.mock import MagicMock
from application.backtest.feed_data import FeedData
import random

chunk_size = random.randint(10,30)
watch_list = ['GALAUSDT','TOMOUSDT','LRCUSDT','ONEUSDT','CRVUSDT','OGNUSDT','RSRUSDT','ENJUSDT','MANAUSDT','CELRUSDT','CTKUSDT','DODOUSDT','ALPHAUSDT','CTSIUSDT','ATAUSDT','IOSTUSDT','AUDIOUSDT','CHZUSDT','HOTUSDT','ARPAUSDT','SFPUSDT','DGBUSDT','FLMUSDT','REEFUSDT','BZRXUSDT','AKROUSDT','LITUSDT','BAKEUSDT','SKLUSDT','BLZUSDT','FTMUSDT','BELUSDT','COTIUSDT','HBARUSDT','GRTUSDT','RENUSDT','KAVAUSDT','SRMUSDT','CELOUSDT','DENTUSDT','BATUSDT','OCEANUSDT','SXPUSDT','ZILUSDT','VETUSDT','XTZUSDT','LINAUSDT','KEEPUSDT','TRXUSDT','ONTUSDT','NKNUSDT','KNCUSDT','XEMUSDT','BTTUSDT','MTLUSDT','ZRXUSDT','IOTAUSDT','MATICUSDT','SANDUSDT','1000XECUSDT','DOGEUSDT','BTSUSDT','C98USDT','TLMUSDT','XLMUSDT','EOSUSDT','STMXUSDT','CVCUSDT','XRPUSDT','1INCHUSDT','RVNUSDT','ICXUSDT','ADAUSDT','NUUSDT','SCUSDT','RLCUSDT','KLAYUSDT','IOTXUSDT','ANKRUSDT','STORJUSDT','CHRUSDT']
watch_list = random.sample(watch_list, random.randint(5,15))

class TestFeedData(TestCase):
    def setUp(self):
        self.feed_data = FeedData(':memory:')
        self.feed_data.database.check_if_symbol_exist = MagicMock()
        self.feed_data.database.get_total_candles_for_one_symbol = MagicMock(return_value = 1000)
        self.feed_data.get_feed = MagicMock()
        self.feed_data.database.prepare_data_on_memory = MagicMock()
        self.feed_data.setup(chunk_size, watch_list)
    
    def test_first_feed_return_dict(self):
        result = self.feed_data.first_feed()
        self.assertIsInstance(result, dict)
        
    def test_first_feed_return_correct_number_of_keys(self):
        result = self.feed_data.first_feed()
        number_of_keys = len(result)
        number_of_watch_list = len(watch_list)
        self.assertEqual(number_of_keys, number_of_watch_list)
        
    def test_feed_return_correct_number_of_keys(self):
        feed = self.feed_data.feed()
        number_of_keys = len(feed)
        number_of_watch_list = len(watch_list)
        self.assertEqual(number_of_keys, number_of_watch_list)