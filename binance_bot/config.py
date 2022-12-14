import configparser

config = configparser.ConfigParser()
config.optionxform = str
config_file = open("config.ini", encoding="utf8")
config.readfp(config_file)

API_KEY = config['binance']['api_key']
API_SECRET = config['binance']['api_secret']

BK_API_KEY = config['bitkub']['api_key']
BK_API_SECRET = config['bitkub']['api_secret']

LINE_NOTIFY_TOKEN = config['line']['notify_token']