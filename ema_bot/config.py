import configparser

config = configparser.ConfigParser(interpolation=None)
config.optionxform = str
config_file = open("config.ini", encoding="utf8")
config.readfp(config_file)

#------------------------------------------------------------
# binance
#------------------------------------------------------------
API_KEY = config['binance']['api_key']
API_SECRET = config['binance']['api_secret']

#------------------------------------------------------------
# bitkub
#------------------------------------------------------------
BK_API_KEY = config['bitkub']['api_key']
BK_API_SECRET = config['bitkub']['api_secret']

#------------------------------------------------------------
# line
#------------------------------------------------------------
LINE_NOTIFY_TOKEN = config['line']['notify_token']

#------------------------------------------------------------
# setting
#------------------------------------------------------------
timeframe = config['setting']['timeframe']
MarginType = config['setting']['margin_type']

Trade_Mode = config['setting']['trade_mode']
Long = config['setting']['trade_long']
Short = config['setting']['trade_short']
automaxLeverage = config['setting']['auto_max_leverage']
Leverage = int(config['setting']['leverage'])
CostType = config['setting']['cost_type']
CostAmount = float(config['setting']['cost_amount'])
limit_Trade = float(config['setting']['limit_trade'])
Not_Trade = float(config['setting']['not_trade'])
TPSL_Mode = config['setting']['tpsl_mode']
TP = float(config['setting']['tp_rate'])
TPclose = float(config['setting']['tp_close'])
SL = float(config['setting']['sl_rate'])
Trailing_Stop_Mode = config['setting']['trailing_stop_mode']
Callback = float(config['setting']['callback'])
Active_TL = float(config['setting']['active_tl_rate'])

Fast_Type = config['setting']['fast_type']
Fast_Value = int(config['setting']['fast_value'])
Slow_Type = config['setting']['slow_type']
Slow_Value = int(config['setting']['slow_value'])
