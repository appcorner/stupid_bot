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

def get_list_float(group, name, default=[]):
    value = default
    try:
        if is_exist(group, name):
            value = [float(x.strip()) for x in config[group][name].split(',')]
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
SANDBOX = (get_str('binance','sandbox', 'off') == 'on')

#------------------------------------------------------------
# line
#------------------------------------------------------------
LINE_NOTIFY_TOKEN = get_str('line','notify_token')
RemovePlot = (get_str('line','remove_plot', 'off') == 'on')
SummaryReport = (get_str('line','summary_report', 'off') == 'on')

#------------------------------------------------------------
# app_config
#------------------------------------------------------------
TIME_SHIFT = get_int('app_config', 'TIME_SHIFT', 5)
CANDLE_LIMIT = get_int('app_config', 'CANDLE_LIMIT', 1000)
CANDLE_PLOT = get_int('app_config', 'CANDLE_PLOT', 100)
LOG_LEVEL = get_int('app_config', 'LOG_LEVEL', 20)
UB_TIMER_MODE = get_int('app_config', 'UB_TIMER_MODE', 4)
if UB_TIMER_MODE < 0 or UB_TIMER_MODE > 5:
    UB_TIMER_MODE = 4
MM_TIMER_MIN = get_float('app_config', 'MM_TIMER_MIN', 0.0)
SWING_TF = get_int('app_config', 'SWING_TF', 5)
SWING_TEST = get_int('app_config', 'SWING_TEST', 2)
TP_FIBO = get_int('app_config', 'TP_FIBO', 2)
CB_AUTO_MODE = get_int('app_config', 'CB_AUTO_MODE', 1)
START_TRADE_TF = get_str('app_config', 'START_TRADE_TF', '4h')

IS_CLEAR_OLD_ORDER = get_str('app_config', 'CLEAR_OLD_ORDER', 'on') == 'on'

#------------------------------------------------------------
# setting
#------------------------------------------------------------
timeframe = get_str('setting', 'timeframe', '5m')
magic_number = get_str('setting', 'magic_number', '12345')

SignalIndex = get_int('setting', 'signal_index', -2)
if SignalIndex > -1 or SignalIndex < -2:
    SignalIndex = -2

# MarginType = get_str('setting', 'margin_type', 'USDT')
MarginType = get_list('setting', 'margin_type', ['USDT'])

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
if is_exist('setting', 'limit_trade') and limit_Trade != 0:
    limit_Trade_Long = 0 # no limit
    limit_Trade_Short = 0 # no limit
else:
    limit_Trade_Long = get_int('setting', 'limit_trade_long', 5)
    limit_Trade_Short = get_int('setting', 'limit_trade_short', 5)
    limit_Trade = 0 # no limit

Not_Trade = get_float('setting', 'not_trade', 10.0)
risk_limit = get_float('setting', 'risk_limit', 0.0)

TPSL_Mode = get_str('setting', 'tpsl_mode', 'on')

TP_Long = get_float('setting', 'tp_long', 0.0)
TP_Short = get_float('setting', 'tp_short', 0.0)

TP_Close_Long = get_float('setting', 'tp_close_long', 50.0)
TP_Close_Short = get_float('setting', 'tp_close_short', 50.0)

# SL = get_float('setting', 'sl_rate')
SL_Long = get_float('setting', 'sl_long', 0.0)
SL_Short = get_float('setting', 'sl_short', 0.0)

Trailing_Stop_Mode = get_str('setting', 'trailing_stop_mode', 'on')

Callback_Long = get_float('setting', 'callback_long', 0.0)
if Callback_Long > 5.0:
    print(f'callback rate ranges from 0.1% to 5%, set to 5.0%')
    Callback_Long = 5.0
elif Callback_Long < 0.1:
    print(f'callback rate ranges from 0.1% to 5%, set to 0.0')
    Callback_Long = 0.0
Callback_Short = get_float('setting', 'callback_short', 0.0)
if Callback_Short > 5.0:
    print(f'callback rate ranges from 0.1% to 5%, set to 5.0%')
    Callback_Short = 5.0
elif Callback_Short < 0.1:
    print(f'callback rate ranges from 0.1% to 5%, set to 0.0')
    Callback_Short = 0.0

Active_TL_Long = get_float('setting', 'active_tl_long', 0.0)
Active_TL_Short = get_float('setting', 'active_tl_short', 0.0)

ADXPeriod = get_int('setting', 'adx_period', 14)
ADXIn = get_int('setting', 'adx_in', 25)

PositionLong = get_str('setting', 'position_long', 'up')
PositionValueLong = get_int('setting', 'position_value_long', 70)
PositionShort = get_str('setting', 'position_short', 'down')
PositionValueShort = get_int('setting', 'position_value_short', 30)

ExitLong = get_str('setting', 'exit_long', 'down')
ExitValueLong = get_int('setting', 'exit_value_long', 50)
ExitShort = get_str('setting', 'exit_short', 'up')
ExitValueShort = get_int('setting', 'exit_value_short', 50)

# MACD_FAST = get_int('setting', 'macd_fast', 12)
# MACD_SLOW = get_int('setting', 'macd_slow', 26)
# MACD_SIGNAL = get_int('setting', 'macd_signal', 9)
RSI_PERIOD = get_int('setting', 'rsi_period', 14)

isSTOOn = get_str('setting', 'sto_mode', 'on') == 'on'
STO_K_PERIOD = get_int('setting', 'sto_k_period', 14)
STO_SMOOTH_K = get_int('setting', 'sto_smooth_k', 3)
STO_D_PERIOD = get_int('setting', 'sto_d_period', 3)

STOEnterLong = get_int('setting', 'sto_enter_long', 20)
STOEnterShort = get_int('setting', 'sto_enter_short', 80)

#------------------------------------------------------------
# hedge
#------------------------------------------------------------
isSidewayTrade = get_str('hedge', 'sideway_trade', 'off') == 'on'

#------------------------------------------------------------
# symbols_setting
#------------------------------------------------------------
CSV_NAME = get_str('symbols_setting', 'csv_name', None)

#------------------------------------------------------------
# mm
#------------------------------------------------------------
is_percent_mode = get_str('mm', 'percent_mode', 'off') == 'on'

TP_PNL_Long = get_float('mm', 'tp_pnl_long', 0.0)
SL_PNL_Long = get_float('mm', 'sl_pnl_long', 0.0)

TP_PNL_Short = get_float('mm', 'tp_pnl_short', 0.0)
SL_PNL_Short = get_float('mm', 'sl_pnl_short', 0.0)

TP_PNL_Close_Long = get_float('mm', 'tp_pnl_close_rate_long', 50.0)
TP_PNL_Close_Short = get_float('mm', 'tp_pnl_close_rate_short', 50.0)

Callback_PNL_Long = get_float('mm', 'callback_pnl_long', 0.0)
if Callback_PNL_Long > 5.0:
    print(f'callback rate ranges from 0.1% to 5%, set to 5.0%')
    Callback_PNL_Long = 5.0
elif Callback_PNL_Long < 0.1:
    print(f'callback rate ranges from 0.1% to 5%, set to 0.0')
    Callback_PNL_Long = 0.0
Callback_PNL_Short = get_float('mm', 'callback_pnl_short', 0.0)
if Callback_PNL_Short > 5.0:
    print(f'callback rate ranges from 0.1% to 5%, set to 5.0%')
    Callback_PNL_Short = 5.0
elif Callback_PNL_Short < 0.1:
    print(f'callback rate ranges from 0.1% to 5%, set to 0.0')
    Callback_PNL_Short = 0.0

Active_TL_PNL_Long = get_float('mm', 'active_tl_pnl_long', 0.0)
Active_TL_PNL_Short = get_float('mm', 'active_tl_pnl_short', 0.0)

average_level = get_int('mm', 'average_level', 0)

TP_Profit = get_float('mm', 'tp_profit', 0.0)
SL_Profit = get_float('mm', 'sl_profit', 0.0)
TP_Profit_Long = get_float('mm', 'tp_profit_long', 0.0)
SL_Profit_Long = get_float('mm', 'sl_profit_long', 0.0)
TP_Profit_Short = get_float('mm', 'tp_profit_short', 0.0)
SL_Profit_Short = get_float('mm', 'sl_profit_short', 0.0)

Clear_Magin = get_float('mm', 'clear_margin', 0.01)

Loss_Limit = get_int('mm', 'loss_limit', 0)