import logging
import json
import datetime

logger_main = ''
logger_activity = ''
now = datetime.datetime.now().__format__('%d%b%Y_%H%M')

def setup_logger(name, level=logging.INFO):
    log_file = name + '.log'
    global logger_main
    logger_main = name
    l = logging.getLogger(name)
    formatter = logging.Formatter(
            '%(name)s\t: %(asctime)s : %(message)s', 
            datefmt='%d-%b-%Y-%H:%M:%S'
        )
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)  

def setup_activity_logger(name, level=logging.INFO):
    # log_file = name + '.log'
    # global logger_activity
    # logger_activity = name
    # l = logging.getLogger(name)
    # formatter = logging.Formatter(
    #         '%(name)s\t: %(asctime)s : \n%(message)s', 
    #         datefmt='%d-%b-%Y-%H:%M:%S'
    #     )
    # fileHandler = logging.FileHandler(log_file, "w")
    # fileHandler.setFormatter(formatter)

    # l.setLevel(level)
    # l.addHandler(fileHandler)
    pass

def logger_main_handler(data):
    log = logging.getLogger(logger_main)
    log.info(data)
 
async def logger_activity_handler(data):
    result = data.to_json(orient="index")
    parsed = json.loads(result)
    file_name = f'order_history/{now}.json'
    with open(file_name, 'w') as f:
        json.dump(parsed, f, indent=4)
