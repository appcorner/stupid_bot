from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock
from strategy.template import TradingStrategy
from application.backtest.backtest_app import BacktestApp
from application.backtest.feed_data import FeedData
from application.backtest.record_trade import RecordTrade
from application.core import Event

class TestBacktestApp(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.backtest_app = BacktestApp(trading_strategy = TradingStrategy(),
                                   feed_data = FeedData(':memory:'),
                                   record_trade = RecordTrade(0.0,0.0))
        self.backtest_app.add_indicators = MagicMock()
        self.backtest_app.trading_strategy.on_candle_closed = AsyncMock()
        self.backtest_app.trading_strategy.on_app_shutdown = AsyncMock()
        self.backtest_app.feed_data.database.get_total_candles_for_one_symbol = MagicMock(return_value = 100)
        self.backtest_app.feed_data.database.check_if_symbol_exist = MagicMock()
        self.backtest_app.feed_data.database.prepare_data_on_memory = MagicMock()
        self.backtest_app.feed_data.get_feed = MagicMock()
        await self.backtest_app.setup()
        
    async def asyncTearDown(self):
        Event.on_send_order -= self.backtest_app.record_order
        
    async def test_setup_first_market_data(self):
        self.assertIsInstance(self.backtest_app.market_data,dict)
    
    async def test_trading_strategy_methods_are_called(self):
        await self.backtest_app.run()
        self.backtest_app.trading_strategy.on_candle_closed.assert_called()
        self.backtest_app.trading_strategy.on_app_shutdown.assert_called_once()
        
    async def test_event_on_send_order_has_record_trade_listener(self):
        self.assertIn(self.backtest_app.record_order, Event.on_send_order.listeners)
        
    async def test_feed_data_chunk_size_same_as_candle_max_length(self):
        feed_data_chunk_size = self.backtest_app.feed_data.chunk_size
        candle_max_length = self.backtest_app.trading_strategy.parameters_on_data.candle_max_length
        self.assertEqual(feed_data_chunk_size,candle_max_length)
        
    async def test_total_cycle_is_called_with_correct_times(self):
        await self.backtest_app.run()
        actually_called = self.backtest_app.trading_strategy.on_candle_closed.call_count
        should_be_called = self.backtest_app.feed_data.database.get_total_candles_for_one_symbol() + 1
        should_be_called -= self.backtest_app.trading_strategy.parameters_on_data.candle_max_length
        self.assertEqual(actually_called, should_be_called)
