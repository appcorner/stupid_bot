import configparser

def is_exist(group, name):
    return group in config.keys() and name in config[group].keys()

def get_list(group, name, default=[]):
    value = default
    try:
        if is_exist(group, name):
            value = [x.strip() for x in config[group][name].split(',')]
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_str(group, name, default=''):
    value = default
    try:
        if is_exist(group, name):
            value = config[group][name]
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_int(group, name, default=0):
    value = default
    try:
        if is_exist(group, name):
            value = int(config[group][name])
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_float(group, name, default=0.0):
    value = default
    try:
        if is_exist(group, name):
            value = float(config[group][name])
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value


config = configparser.ConfigParser(interpolation=None)
config.optionxform = str
config_file = open("config.ini", mode='r', encoding='utf-8-sig')
config.readfp(config_file)

#------------------------------------------------------------
# binance
#------------------------------------------------------------
API_KEY = get_str('binance','api_key')
API_SECRET = get_str('binance','api_secret')

#------------------------------------------------------------
# line
#------------------------------------------------------------
LINE_NOTIFY_TOKEN = get_str('line','notify_token')

#------------------------------------------------------------
# app_config
#------------------------------------------------------------
TIME_SHIFT = get_int('app_config', 'TIME_SHIFT', 5)
CANDLE_LIMIT = get_int('app_config', 'CANDLE_LIMIT', 1000)
CANDLE_PLOT = get_int('app_config', 'CANDLE_PLOT', 100)
LOG_LEVEL = get_int('app_config', 'LOG_LEVEL', 20)

#------------------------------------------------------------
# setting
#------------------------------------------------------------
timeframe = get_str('setting', 'timeframe', '5m')

SignalIndex = get_int('setting', 'signal_index', -2)
if SignalIndex > -1 or SignalIndex < -2:
    SignalIndex = -2

MarginType = get_str('setting', 'margin_type', 'USDT')

watch_list = get_list('setting', 'watch_list')
back_list = get_list('setting', 'back_list')

Trade_Mode = get_str('setting', 'trade_mode', 'off')
Long = get_str('setting', 'trade_long', 'on')
Short = get_str('setting', 'trade_short', 'on')
automaxLeverage = get_str('setting', 'auto_max_leverage', 'off')
Leverage = get_int('setting', 'leverage', 20)
CostType = get_str('setting', 'cost_type', '$')
CostAmount = get_float('setting', 'cost_amount', 1.5)
limit_Trade = get_int('setting', 'limit_trade', 10)
Not_Trade = get_float('setting', 'not_trade', 10.0)
TPSL_Mode = get_str('setting', 'tpsl_mode', 'on')
# TP = get_float('setting', 'tp_rate')
TP_Long = get_float('setting', 'tp_long', 10.0)
TP_Short = get_float('setting', 'tp_short', 10.0)

TPclose = get_float('setting', 'tp_close', 50.0)
TPclose_Long = TPclose
TPclose_Short = TPclose
if is_exist('setting', 'tp_close_long'):
    TPclose_Long = get_float('setting', 'tp_close_long', 50.0)
if is_exist('setting', 'tp_close_short'):
    TPclose_Short = get_float('setting', 'tp_close_short', 50.0)

# SL = get_float('setting', 'sl_rate')
SL_Long = get_float('setting', 'sl_long', 4.0)
SL_Short = get_float('setting', 'sl_short', 4.0)

Trailing_Stop_Mode = get_str('setting', 'trailing_stop_mode', 'on')

Callback = get_float('setting', 'callback', 5.0)
Callback_Long = Callback
Callback_Short = Callback
if is_exist('setting', 'callback_long'):
    Callback_Long = get_float('setting', 'callback_long', 5.0)
if is_exist('setting', 'callback_short'):
    Callback_Short = get_float('setting', 'callback_short', 5.0)

Active_TL = get_float('setting', 'active_tl_rate', 10.0)
Active_TL_Long = Active_TL
Active_TL_Short = Active_TL
if is_exist('setting', 'active_tl_long'):
    Active_TL_Long = get_float('setting', 'active_tl_long', 10.0)
if is_exist('setting', 'active_tl_short'):
    Active_TL_Short = get_float('setting', 'active_tl_short', 10.0)

Fast_Type = get_str('setting', 'fast_type')
Fast_Value = get_int('setting', 'fast_value')
Mid_Type = get_str('setting', 'mid_type')
Mid_Value = get_int('setting', 'mid_value')
Slow_Type = get_str('setting', 'slow_type')
Slow_Value = get_int('setting', 'slow_value')

MACD_FAST = get_int('setting', 'macd_fast')
MACD_SLOW = get_int('setting', 'macd_slow')
MACD_SIGNAL = get_int('setting', 'macd_signal')
RSI_PERIOD = get_int('setting', 'rsi_period')

CSV_NAME = get_str('symbols_setting', 'csv_name', None)

TP_IfPNL_Gt = get_float('mm', 'tp_if_pnl_gt', 0.0)
SL_IfPNL_Lt = get_float('mm', 'sl_if_pnl_lt', 0.0)

TP_IfAllProfit_Gt = get_float('mm', 'tp_if_all_profit_gt', 0.0)
SL_IfAllProfit_Lt = get_float('mm', 'sl_if_all_profit_lt', 0.0)

TP_IfLongProfit_Gt = get_float('mm', 'tp_if_long_profit_gt', 0.0)
SL_IfLongProfit_Lt = get_float('mm', 'sl_if_long_profit_lt', 0.0)

TP_IfShortProfit_Gt = get_float('mm', 'tp_if_short_profit_gt', 0.0)
SL_IfShortProfit_Lt = get_float('mm', 'sl_if_short_profit_lt', 0.0)

Loss_Limit = get_int('mm', 'loss_limit', 0)