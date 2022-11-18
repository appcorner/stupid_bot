import configparser

def get_list(group, name, default=[]):
    value = default
    if group in config.keys() and name in config[group].keys():
        value = [x.strip() for x in config[group][name].split(',')]
    else:
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_str(group, name, default=''):
    value = default
    if group in config.keys() and name in config[group].keys():
        value = config[group][name]
    else:
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_int(group, name, default=0):
    value = default
    if group in config.keys() and name in config[group].keys():
        value = int(config[group][name])
    else:
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_float(group, name, default=0.0):
    value = default
    if group in config.keys() and name in config[group].keys():
        value = float(config[group][name])
    else:
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
# bitkub
#------------------------------------------------------------
# BK_API_KEY = get_str('bitkub','api_key')
# BK_API_SECRET = get_str('bitkub','api_secret')

#------------------------------------------------------------
# line
#------------------------------------------------------------
LINE_NOTIFY_TOKEN = get_str('line','notify_token')

#------------------------------------------------------------
# setting
#------------------------------------------------------------
timeframe = get_str('setting', 'timeframe')

SignalIndex = get_int('setting', 'signal_index', -2)
if SignalIndex > -1 or SignalIndex < -2:
    SignalIndex = -2

MarginType = get_str('setting', 'margin_type')

watch_list = get_list('setting', 'watch_list')
back_list = get_list('setting', 'back_list')

Trade_Mode = get_str('setting', 'trade_mode')
Long = get_str('setting', 'trade_long')
Short = get_str('setting', 'trade_short')
automaxLeverage = get_str('setting', 'auto_max_leverage')
Leverage = get_int('setting', 'leverage')
CostType = get_str('setting', 'cost_type')
CostAmount = get_float('setting', 'cost_amount')
limit_Trade = get_float('setting', 'limit_trade')
Not_Trade = get_float('setting', 'not_trade')
TPSL_Mode = get_str('setting', 'tpsl_mode')
TP = get_float('setting', 'tp_rate')
TPclose = get_float('setting', 'tp_close')
SL = get_float('setting', 'sl_rate')
Trailing_Stop_Mode = get_str('setting', 'trailing_stop_mode')
Callback = get_float('setting', 'callback')
Active_TL = get_float('setting', 'active_tl_rate')

Fast_Type = get_str('setting', 'fast_type')
Fast_Value = get_int('setting', 'fast_value')
Mid_Type = get_str('setting', 'mid_type')
Mid_Value = get_int('setting', 'mid_value')
Slow_Type = get_str('setting', 'slow_type')
Slow_Value = get_int('setting', 'slow_value')
