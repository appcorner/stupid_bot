# -*- coding: utf-8 -*-

from asyncio import get_event_loop, gather, sleep
import numpy as np
import pandas as pd
import pandas_ta as ta
import time
import mplfinance as mpf
import matplotlib.pyplot as plt
from LineNotify import LineNotify
import os
import pathlib
import logging
from logging.handlers import RotatingFileHandler
from random import randint, shuffle
from datetime import datetime
import json
from uuid import uuid4

# -----------------------------------------------------------------------------
# API_KEY, API_SECRET, LINE_NOTIFY_TOKEN in config.ini
# -----------------------------------------------------------------------------

import ccxt.async_support as ccxt

import config

# print('CCXT Version:', ccxt.__version__)
# -----------------------------------------------------------------------------

bot_name = 'ADX+RSI+STO'
bot_vesion = '1.5.3b'

bot_fullname = f'{bot_name} Futures (Binance) version {bot_vesion}'

# ansi escape code
CLS_SCREEN = '\033[2J\033[1;1H' # cls + set top left
CLS_LINE = '\033[0J'
SHOW_CURSOR = '\033[?25h'
HIDE_CURSOR = '\033[?25l'
CRED  = '\33[31m'
CGREEN  = '\33[32m'
CYELLOW  = '\33[33m'
CEND = '\033[0m'
CBOLD = '\33[1m'

# กำหนดเวลาที่ต้องการเลื่อนการอ่านข้อมูล เป็นจำนวนวินาที
TIME_SHIFT = config.TIME_SHIFT

TIMEFRAME_SECONDS = {
    '1m': 60,
    '3m': 60*3,
    '5m': 60*5,
    '15m': 60*15,
    '30m': 60*30,
    '1h': 60*60,
    '2h': 60*60*2,
    '4h': 60*60*4,
    '6h': 60*60*6,
    '8h': 60*60*8,
    '12h': 60*60*12,
    '1d': 60*60*24,
}

CANDLE_PLOT = config.CANDLE_PLOT
CANDLE_SAVE = CANDLE_PLOT + max(config.ADXPeriod,config.RSI_PERIOD,config.STO_K_PERIOD)
CANDLE_LIMIT = max(config.CANDLE_LIMIT,CANDLE_SAVE)

UB_TIMER_SECONDS = [
    TIMEFRAME_SECONDS[config.timeframe],
    15,
    20,
    30,
    60,
    int(TIMEFRAME_SECONDS[config.timeframe]/2)
]

POSITION_COLUMNS = ["symbol", "entryPrice", "positionAmt", "initialMargin", "leverage", "unrealizedProfit"]
POSITION_COLUMNS_RENAME = ["Symbol", "Entry Price", "Amount", "Margin", "Leverage", "Unrealized PNL", "Side", "Quote", "Orders"]
POSITION_COLUMNS_DISPLAY = ["Symbol", "Side", "Entry Price", "Amount", "Margin", "Leverage", "Unrealized PNL", "Orders"]

CSV_COLUMNS = [
        "symbol", "signal_index", "margin_type",
        "trade_mode", "trade_long", "trade_short",
        "leverage", "cost_type", "cost_amount",
        "tpsl_mode",
        "tp_long", "tp_short",
        "tp_close_long", "tp_close_short",
        "sl_long", "sl_short",
        "trailing_stop_mode",
        "callback_long", "callback_short",
        "active_tl_long", "active_tl_short",
        "adx_period", "adx_in",
        "sto_k_period", "sto_smooth_k", "sto_d_period",
        "position_long", "position_value_long", "position_short", "position_value_short",
        "exit_long", "exit_value_long", "exit_short", "exit_value_short",
        "sto_enter_long", "sto_enter_short"
        ]

DATE_SUFFIX = datetime.now().strftime("%Y%m%d_%H%M%S")

# ----------------------------------------------------------------------------
# global variable
# ----------------------------------------------------------------------------
notify = LineNotify(config.LINE_NOTIFY_TOKEN)

all_positions = pd.DataFrame(columns=POSITION_COLUMNS)
count_trade = 0
count_trade_long = 0
count_trade_short = 0

start_balance_total = 0.0
balalce_total = 0.0
balance_entry = {}

watch_list = []
all_symbols = {}
all_candles = {}

orders_history = {}

total_risk = {}
total_margin = {}
is_send_notify_risk = False

is_positionside_dual = False

is_send_notify_error = True
last_error_message = ''
symbols_setting = pd.DataFrame(columns=CSV_COLUMNS)

history_file_csv = 'orders_history.csv'
history_json_path = 'orders_history.json'

async def getExchange():
    exchange = ccxt.binance({
        "apiKey": config.API_KEY,
        "secret": config.API_SECRET,
        "options": {"defaultType": "future", "adjustForTimeDifference": True},
        "enableRateLimit": True}
    )
    if config.SANDBOX:
        exchange.set_sandbox_mode(True)
    try:
        await exchange.load_time_difference()
    except:
        pass
    return exchange

def school_round(a_in,n_in):
    ''' python uses "banking round; while this round 0.05 up '''
    if (a_in * 10 ** (n_in + 1)) % 10 == 5:
        return round(a_in + 1 / 10 ** (n_in + 1), n_in)
    else:
        return round(a_in, n_in)

def amount_to_precision(symbol, amount_value):
    amount_precision = all_symbols[symbol]['amount_precision']
    amount = school_round(amount_value, amount_precision)
    return amount
def price_to_precision(symbol, price_value):
    price_precision = all_symbols[symbol]['price_precision']
    price = school_round(price_value, price_precision)
    return price

def cal_callback_rate(symbol, closePrice, targetPrice):
    rate = round(abs(closePrice - targetPrice) / closePrice * 100.0, 1)
    logger.debug(f'{symbol} closePrice:{closePrice}, targetPrice:{targetPrice}, callback_rate:{rate}')
    if rate > 5.0:
        return 5.0
    elif rate < 0.1:
        return 0.1
    else:
        return rate

def cal_minmax_fibo(symbol, df, pd='', entryPrice=0.0, digits=5):
    iday = df.tail(CANDLE_PLOT)
    
    entryPrice = iday['close'].iloc[-1] if entryPrice == 0.0 else entryPrice
    
    # swing low
    periods = 3
    lows_list = list(iday['low'])
    lows_list.reverse()
    # logger.debug(lows_list)
    # swing_low = lows_list[0]
    swing_lows = []
    for i in range(len(lows_list)):
        if i >= periods:
            # Check if the current price is the lowest in the last `periods` periods
            if min(lows_list[i-periods:i+1]) == lows_list[i]:
                swing_lows.append(lows_list[i])
    # logger.debug(swing_lows)

    signalIdx = config.SignalIndex
    if symbol in symbols_setting.index:
        signalIdx = int(symbols_setting.loc[symbol]['signal_index'])

    iday_minmax = iday[:CANDLE_PLOT+signalIdx]
    minimum_index = iday_minmax['low'].idxmin()
    minimum_price = iday_minmax['low'].min()
    maximum_index = iday_minmax['high'].idxmax()
    maximum_price = iday_minmax['high'].max()
    #Calculate the max high and min low price
    difference = maximum_price - minimum_price #Get the difference

    # fibo_values = [0,0.1618,0.236,0.382,0.5,0.618,0.786,1,1.382]
    fibo_values = [0,0.236,0.382,0.5,0.618,0.786,1,1.382]

    isFiboRetrace = True
    minmax_points = []
    fibo_levels = []
    periods = config.SWING_TF
    swing_lows = []
    swing_highs = []
    tp = 0.0
    sl = 0.0

    # logger.debug(minimum_index)
    # logger.debug(maximum_index)

    # iday_minmax['sw_low'] = np.nan
    # iday_minmax['sw_high'] = np.nan
    for i in range(len(iday_minmax)):
        if i >= periods:
            if min(iday_minmax['low'].iloc[i-periods:i+1+periods]) == iday_minmax['low'].iloc[i]:
                swing_lows.append(iday_minmax['low'].iloc[i])
                # iday_minmax['sw_low'].iloc[i] =  iday_minmax['low'].iloc[i]
            if max(iday_minmax['high'].iloc[i-periods:i+1+periods]) == iday_minmax['high'].iloc[i]:
                swing_highs.append(iday_minmax['high'].iloc[i])
                # iday_minmax['sw_high'].iloc[i] =  iday_minmax['low'].iloc[i]

    if 'long' in pd.lower():
        isFiboRetrace = datetime.strptime(str(minimum_index), '%Y-%m-%d %H:%M:%S%z') > datetime.strptime(str(maximum_index), '%Y-%m-%d %H:%M:%S%z')
        # print(isFiboRetrace)

        if isFiboRetrace:
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((minimum_index,minimum_price))
            for idx, fibo_val in enumerate(fibo_values):
                fibo_level = price_to_precision(symbol, minimum_price + difference * fibo_val)
                fibo_levels.append(fibo_level)
                if tp == 0.0 and entryPrice < fibo_level:
                    tp_fibo = min(idx+config.TP_FIBO, len(fibo_values)-1)
                    tp = price_to_precision(symbol, minimum_price + difference * fibo_values[tp_fibo])
        else:
            # maxidx = np.where(iday_minmax.index==maximum_index)[0][0]
            maxidx = iday_minmax.index.get_loc(maximum_index)
            # print(maxidx)
            if maxidx < len(iday_minmax)-1:
                new_minimum_index = iday_minmax['low'].iloc[maxidx+1:].idxmin()
                new_minimum_price = iday_minmax['low'].iloc[maxidx+1:].min()
            else:
                new_minimum_index = iday_minmax['low'].iloc[maxidx:].idxmin()
                new_minimum_price = iday_minmax['low'].iloc[maxidx:].min()
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((new_minimum_index,new_minimum_price))
            for idx, fibo_val in enumerate(fibo_values):
                fibo_level = price_to_precision(symbol, new_minimum_price + difference * fibo_val)
                fibo_levels.append(fibo_level)
                if tp == 0.0 and entryPrice < fibo_level:
                    tp_fibo = min(idx+config.TP_FIBO, len(fibo_values)-1)
                    tp = price_to_precision(symbol, new_minimum_price + difference * fibo_values[tp_fibo])

        sl_fibo = entryPrice - difference * fibo_values[1]
        sl_sw = min(swing_lows[-config.SWING_TEST:])
        sl = min(sl_fibo, sl_sw)

    elif 'short' in pd.lower() :
        isFiboRetrace = datetime.strptime(str(minimum_index), '%Y-%m-%d %H:%M:%S%z') < datetime.strptime(str(maximum_index), '%Y-%m-%d %H:%M:%S%z')
        # print(isFiboRetrace)

        if isFiboRetrace:
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((maximum_index,maximum_price))
            for idx, fibo_val in enumerate(fibo_values):
                fibo_level = price_to_precision(symbol, maximum_price - difference * fibo_val)
                fibo_levels.append(fibo_level)
                if tp == 0.0 and entryPrice > fibo_level:
                    tp_fibo = min(idx+config.TP_FIBO, len(fibo_values)-1)
                    tp = price_to_precision(symbol, maximum_price - difference * fibo_values[tp_fibo])
        else:
            # minidx = np.where(iday_minmax.index==minimum_index)[0][0]
            minidx = iday_minmax.index.get_loc(minimum_index)
            # print(maxidx)
            if minidx < len(iday_minmax)-1:
                new_maximum_index = iday_minmax['high'].iloc[minidx+1:].idxmax()
                new_maximum_price = iday_minmax['high'].iloc[minidx+1:].max()
            else:
                new_maximum_index = iday_minmax['high'].iloc[minidx:].idxmax()
                new_maximum_price = iday_minmax['high'].iloc[minidx:].max()
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((new_maximum_index,new_maximum_price))
            for idx, fibo_val in enumerate(fibo_values):
                fibo_level = price_to_precision(symbol, new_maximum_price - difference * fibo_val)
                fibo_levels.append(fibo_level)
                if tp == 0.0 and entryPrice > fibo_level:
                    tp_fibo = min(idx+config.TP_FIBO, len(fibo_values)-1)
                    tp = price_to_precision(symbol, new_maximum_price - difference * fibo_values[tp_fibo])

        sl_fibo = entryPrice + difference * fibo_values[1]
        sl_sw = max(swing_highs[-config.SWING_TEST:])
        sl = max(sl_fibo, sl_sw)

    if config.CB_AUTO_MODE == 1:
        callback_rate = cal_callback_rate(symbol, entryPrice, tp)
    else:
        callback_rate = cal_callback_rate(symbol, entryPrice, sl)

    return {
        'fibo_type': 'retractment' if isFiboRetrace else 'extension',
        'difference': difference,
        'min_max': minmax_points, 
        'fibo_values': fibo_values,
        'fibo_levels': fibo_levels,
        'swing_highs': swing_highs,
        'swing_lows': swing_lows,
        'tp': round(tp, digits),
        'sl': round(sl, digits),
        'price': round(entryPrice, digits),
        'tp_txt': '-',
        'sl_txt': '-',
        'price_txt': 'Price: @{}'.format(round(entryPrice, digits)),
        'callback_rate': callback_rate
    }

async def line_chart(symbol, df, msg, pd='', fibo_data=None, **kwargs):
    try:
        plt.rcdefaults()

        print(f"{symbol} create line_chart")
        data = df.tail(CANDLE_PLOT)

        showFibo = fibo_data != None and 'exit' not in pd.lower()

        ADXLine = [kwargs['ADXIn'] for i in range(0, CANDLE_PLOT)]
        RSIlo = [kwargs['RSIlo'] for i in range(0, CANDLE_PLOT)]
        RSIhi = [kwargs['RSIhi'] for i in range(0, CANDLE_PLOT)]
        STOlo = [kwargs['STOlo'] for i in range(0, CANDLE_PLOT)]
        STOhi = [kwargs['STOhi'] for i in range(0, CANDLE_PLOT)]

        # colors = ['green' if value >= 0 else 'red' for value in data['MACD']]
        added_plots = [
            mpf.make_addplot(data['RSI'],ylim=(10, 90),panel=2,color='blue',width=0.75,
                fill_between=dict(y1=kwargs['RSIlo'], y2=kwargs['RSIhi'], color="orange"),
                ylabel=f"RSI ({config.RSI_PERIOD})", y_on_right=False),
            mpf.make_addplot(RSIlo,ylim=(10, 90),panel=2,color='red',linestyle='-.',width=0.5),
            mpf.make_addplot(RSIhi,ylim=(10, 90),panel=2,color='red',linestyle='-.',width=0.5),

            mpf.make_addplot(data['ADX'],ylim=(0, 90),panel=3,color='red',width=0.75,
                ylabel=f"ADX ({config.ADXPeriod})", y_on_right=True),
            mpf.make_addplot(ADXLine,ylim=(0, 90),panel=3,color='red',linestyle='-.',width=0.5),

            mpf.make_addplot(data['STOCHk'],ylim=(0, 100),panel=4,color='blue',width=0.75,
                fill_between=dict(y1=kwargs['STOlo'], y2=kwargs['STOhi'], color="orange"),
                ylabel=f"STO ({config.STO_K_PERIOD})", y_on_right=False),
            mpf.make_addplot(data['STOCHd'],ylim=(0, 100),panel=4,color='red',width=0.75),
            mpf.make_addplot(STOlo,ylim=(0, 100),panel=4,color='red',linestyle='-.',width=0.5),
            mpf.make_addplot(STOhi,ylim=(0, 100),panel=4,color='red',linestyle='-.',width=0.5),
        ]

        if config.isSTOOn:
            added_plots.append(mpf.make_addplot(data['SMAhi'],panel=0,color='orange',width=0.75))
            added_plots.append(mpf.make_addplot(data['SMAlo'],panel=0,color='cyan',width=0.75))

        kwargs = dict(
            figscale=1.2,
            figratio=(8, 7),
            panel_ratios=(8,1,2,1,2),
            addplot=added_plots,
            # tight_layout=True,
            # scale_padding={'left': 0.5, 'top': 2.5, 'right': 2.5, 'bottom': 0.75},
            scale_padding={'left': 0.5, 'top': 0.6, 'right': 1.0, 'bottom': 0.5},
            )

        fibo_title = ''

        if showFibo:
            # fibo_colors = ['red','brown','orange','gold','green','blue','gray','purple','purple','purple']
            logger.debug(fibo_data)
            # fibo_colors.append('g')
            # fibo_data['fibo_levels'].append(fibo_data['swing_highs'][0])
            # fibo_colors.append('r')
            # fibo_data['fibo_levels'].append(fibo_data['swing_lows'][0])
            # fibo_lines = dict(
            #     hlines=fibo_data['fibo_levels'],
            #     colors=fibo_colors,
            #     alpha=0.5,
            #     linestyle='-.',
            #     linewidths=1,
            #     )
            tpsl_colors = []
            tpsl_data = []
            if 'tp' in fibo_data.keys() and fibo_data['tp'] > 0:
                tpsl_colors.append('g')
                tpsl_data.append(fibo_data['tp'])
            if 'sl' in fibo_data.keys() and fibo_data['sl'] > 0:
                tpsl_colors.append('r')
                tpsl_data.append(fibo_data['sl'])
            if 'price' in fibo_data.keys():
                tpsl_colors.append('b')
                tpsl_data.append(fibo_data['price'])
            if len(tpsl_data) > 0:
                tpsl_lines = dict(
                    hlines=tpsl_data,
                    colors=tpsl_colors,
                    alpha=0.5,
                    linestyle='-.',
                    linewidths=1,
                    )
                kwargs['hlines']=tpsl_lines

            if 'min_max' in fibo_data.keys():
                minmax_lines = dict(
                    alines=fibo_data['min_max'],
                    colors='black',
                    linestyle='--',
                    linewidths=0.1,
                    )
                kwargs['alines']=minmax_lines

            if 'fibo_type' in fibo_data.keys():
                fibo_title = ' fibo-'+fibo_data['fibo_type'][0:2]

        myrcparams = {'axes.labelsize':10,'xtick.labelsize':8,'ytick.labelsize':8}
        mystyle = mpf.make_mpf_style(base_mpf_style='charles',rc=myrcparams)

        fig, axlist = mpf.plot(
            data,
            volume=True,volume_panel=1,
            **kwargs,
            type="candle",
            xrotation=0,
            ylabel='Price',
            style=mystyle,
            returnfig=True,
        )
        # print(axlist)
        ax1,*_ = axlist

        title = ax1.set_title(f'{symbol} {pd} ({config.timeframe} @ {data.index[-1]}{fibo_title})')
        title.set_fontsize(14)

        if showFibo:
            if 'difference' in fibo_data.keys():
                difference = fibo_data['difference']
            else:
                difference = 0.0
            
            if 'fibo_levels' in fibo_data.keys():
                fibo_colors = ['red','brown','orange','gold','green','blue','gray','purple','purple','purple']
                fibo_levels = fibo_data['fibo_levels']
                for idx, fibo_val in enumerate(fibo_data['fibo_values']):
                    if idx < len(fibo_levels)-1:
                        ax1.fill_between([0, CANDLE_PLOT] ,fibo_levels[idx],fibo_levels[idx+1],color=fibo_colors[idx],alpha=0.1)
                    ax1.text(0,fibo_levels[idx] + difference * 0.02,f'{fibo_val}({fibo_levels[idx]:.2f})',fontsize=8,color=fibo_colors[idx],horizontalalignment='left')

            none_tpsl_txt = []
            if 'tp' in fibo_data.keys() and fibo_data['tp'] > 0:
                fibo_tp = fibo_data['tp']
                fibo_tp_txt = fibo_data['tp_txt']
                ax1.text(CANDLE_PLOT/2,fibo_tp - difference * 0.06,fibo_tp_txt,fontsize=8,color='g',horizontalalignment='center')
            else:
                none_tpsl_txt.append('No TP')

            if 'sl' in fibo_data.keys() and fibo_data['sl'] > 0:
                fibo_sl = fibo_data['sl']
                fibo_sl_txt = fibo_data['sl_txt']
                ax1.text(CANDLE_PLOT/2,fibo_sl - difference * 0.06,fibo_sl_txt,fontsize=8,color='r',horizontalalignment='center')
            else:
                none_tpsl_txt.append('No SL')
                
            if 'price' in fibo_data.keys():
                fibo_price = fibo_data['price']
                fibo_price_txt = fibo_data['price_txt'] + (' [' + ','.join(none_tpsl_txt) + ']' if len(none_tpsl_txt) > 0 else '')
                ax1.text(CANDLE_PLOT/2,fibo_price - difference * 0.06,fibo_price_txt,fontsize=8,color='b',horizontalalignment='center')

        filename = f"./plots/order_{symbol}_{pd}.png"
        fig.savefig(filename)

        plt.close(fig)

        # await sleep(3)
        notify.Send_Image(msg, image_path=filename, remove_file=config.RemovePlot)

    except Exception as ex:
        print(type(ex).__name__, symbol, str(ex))
        logger.exception(f'line_chart {symbol}')

    return

async def line_report(marginType, positions, report_summary, is_profitable=True):
    try:
        plt.rcdefaults()

        fig, ax = plt.subplots(figsize=(8, 6))
        plt.autoscale()

        cell_text = []
        for row in range(len(positions)):
            cell_text.append(positions.iloc[row])

        the_table = ax.table(cellText=cell_text, colLabels=positions.columns, loc='center')
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(16)
        the_table.scale(2.25, 2)
        # Get the extent of the table and its surrounding axes
        fig.canvas.draw()
        extent = the_table.get_window_extent(fig.canvas.renderer).transformed(fig.dpi_scale_trans.inverted())

        for col in ['Symbol', 'Entry Price', 'Amount', 'Margin']:
            col_idx = positions.columns.get_loc(col)
            # the_table[0, col_idx].get_text().set_color('white')
            the_table[0, col_idx].set_facecolor("#ebebeb")
            # the_table[0, col_idx].set_alpha(0.1)

        for col in ['Side', 'Leverage', 'Unrealized PNL', 'Orders']:
            col_idx = positions.columns.get_loc(col)
            # the_table[0, col_idx].get_text().set_color('white')
            the_table[0, col_idx].set_facecolor("#cfcfcf")
            # the_table[0, col_idx].set_alpha(0.1)

        col_idx = positions.columns.get_loc('Unrealized PNL')
        for row in range(len(positions)):
            cell_color = '#f8e0e0'
            if float(positions.iloc[row, col_idx]) >= 0:
                cell_color = '#e6f8e0'
            for col in range(len(positions.columns)):
                # the_table[row+1, col].get_text().set_color(cell_color)
                the_table[row+1, col].set_facecolor(cell_color)
                # the_table[row+1, col].set_alpha(0.1)

        # Calculate the height of the table
        table_height = extent.height / fig.dpi
        # Set the y value for the text based on the height of the table
        text_y = -table_height - 0.05
        text_head = table_height
        ax.set_axis_off()
        bot_title = f"{bot_fullname} - {config.timeframe} - {marginType}"
        plt.text(0, text_head+0.04, "My Profit & Loss", fontsize=36, color='#f1b90d', backgroundcolor='black', fontweight='bold', ha='center')
        if is_profitable:
            plt.text(0, text_y-0.04, report_summary, fontsize=16, ha='center', fontweight='bold', color='#5858fa')
        else:
            plt.text(0, text_y-0.04, report_summary, fontsize=16, ha='center', fontweight='bold', color='#fa5858')
        plt.text(0, text_y-0.06, bot_title, fontsize=14, ha='center')

        # fig.tight_layout()
        
        filename = f"./plots/reports_{marginType}.png"
        fig.savefig(filename, bbox_inches='tight')

        plt.close(fig)

        # await sleep(3)
        notify.Send_Image('Table Profit', image_path=filename, remove_file=config.RemovePlot)

    except Exception as ex:
        print(type(ex).__name__, marginType, str(ex))
        logger.exception(f'line_report {marginType}')

def line_notify_err(message):
    global is_send_notify_error, last_error_message
    is_send_notify_error = config.is_notify_api_error and is_send_notify_error
    if is_send_notify_error:
        if '"code":-2015' in str(message):
            if 'request ip:' in str(message):
                line_notify(message)
        else:
            line_notify(message)
        is_send_notify_error = False
        last_error_message = ''
    else:
        last_error_message = message
def line_notify_last_err():
    global is_send_notify_error, last_error_message
    if len(last_error_message):
        if '"code":-2015' in str(last_error_message):
            return
        line_notify(last_error_message)
    is_send_notify_error = True
    last_error_message = ''

def line_notify(message):
    try:
        log_message = message.replace('\n', ',')
        logger.info(f'{log_message}')
        notify.Send_Text(message)
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception(f'line_notify')

    return

def add_indicator(symbol, bars):
    df = pd.DataFrame(
        bars, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).map(
        lambda x: x.tz_convert("Asia/Bangkok")
    )
    df = df.set_index("timestamp")

    # เอาข้อมูลใหม่ไปต่อท้าย ข้อมูลที่มีอยู่
    if symbol in all_candles.keys() and len(df) < CANDLE_LIMIT:
        df = pd.concat([all_candles[symbol], df], ignore_index=False)

        # เอาแท่งซ้ำออก เหลืออันใหม่สุด
        df = df[~df.index.duplicated(keep='last')].tail(CANDLE_LIMIT)

    df = df.tail(CANDLE_LIMIT)

    if symbol in all_candles.keys() and len(df) < CANDLE_SAVE:
        print(f'less candles for {symbol}, skip add_indicator')
        return df

    # คำนวนค่าต่างๆใหม่
    df['ADX'] = 0
    df['RSI'] = 0
    # df['MACD'] = 0
    # df['MACDs'] = 0
    # df['MACDh'] = 0

    try:
        ADXPeriod = config.ADXPeriod 

        if symbol in symbols_setting.index:
            ADXPeriod = symbols_setting.loc[symbol]['adx_period']

        # cal MACD
        # ewm_fast     = df['close'].ewm(span=config.MACD_FAST, adjust=False).mean()
        # ewm_slow     = df['close'].ewm(span=config.MACD_SLOW, adjust=False).mean()
        # df['MACD']   = ewm_fast - ewm_slow
        # df['MACDs']  = df['MACD'].ewm(span=config.MACD_SIGNAL).mean()
        # df['MACDh']  = df['MACD'] - df['MACDs']

        # cal ADX
        adx = ta.adx(df['high'],df['low'],df['close'],ADXPeriod)
        df['ADX']= adx[f'ADX_{ADXPeriod}']

        # cal RSI
        df["RSI"] = ta.rsi(df['close'],config.RSI_PERIOD)

        # cal SMA
        df['SMAhi'] = ta.sma(df['high'], config.SMA_PERIOD_HIGH)
        df['SMAlo'] = ta.sma(df['low'], config.SMA_PERIOD_LOW)

        # cal STO
        stoch_k = f'STOCHk_{config.STO_K_PERIOD}_{config.STO_D_PERIOD}_{config.STO_SMOOTH_K}'
        stoch_d = f'STOCHd_{config.STO_K_PERIOD}_{config.STO_D_PERIOD}_{config.STO_SMOOTH_K}'
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=config.STO_K_PERIOD, d=config.STO_D_PERIOD, smooth_k=config.STO_SMOOTH_K)
        df['STOCHk'] = stoch[stoch_k]
        df['STOCHd'] = stoch[stoch_d]

    except Exception as ex:
        print(type(ex).__name__, symbol, str(ex))
        logger.exception(f'add_indicator {symbol}')

    return df

def patch_symbol(symbol:str, quote:str):
    symbol_arr = f'{symbol}:{quote}'.split(':')
    return ':'.join(symbol_arr[0:2])

def exchange_symbol(symbol):
    # return ':'.join([all_symbols[symbol]['symbol'],all_symbols[symbol]['quote']])
    return all_symbols[symbol]['symbol']
    # return symbol

"""
fetch_ohlcv - อ่านแท่งเทียน
exchange: binance exchange
symbol: coins symbol
timeframe: candle time frame
limit: จำนวนแท่งที่ต้องการ, ใส่ 0 หากต้องการให้เอาแท่งใหม่ที่ไม่มาครบ
timestamp: ระบุเวลาปัจจุบัน ถ้า limit=0
"""
async def fetch_ohlcv(exchange, symbol, timeframe, limit=1, timestamp=0):
    global all_candles
    try:
        # กำหนดการอ่านแท่งเทียนแบบไม่ระบุจำนวน
        if limit == 0 and symbol in all_candles.keys():
            timeframe_secs = TIMEFRAME_SECONDS[timeframe]
            last_candle_time = int(pd.Timestamp(all_candles[symbol].index[-1]).tz_convert('UTC').timestamp())
            # ให้อ่านแท่งสำรองเพิ่มอีก 2 แท่ง
            ohlcv_bars = await exchange.fetch_ohlcv(symbol, timeframe, None, round(1.5+(timestamp-last_candle_time)/timeframe_secs))
        else:
            ohlcv_bars = await exchange.fetch_ohlcv(symbol, timeframe, None, limit)
        if len(ohlcv_bars):
            all_candles[symbol] = add_indicator(symbol, ohlcv_bars)
            # print(symbol)
    except Exception as ex:
        print(type(ex).__name__, symbol, str(ex))
        logger.exception(f'fetch_ohlcv {symbol}')
        line_notify_err(f'แจ้งปัญหาเหรียญ {symbol}:\nการอ่านแท่งเทียนผิดพลาด: {str(ex)}')
        if limit == 0 and symbol in all_candles.keys():
            print('----->', timestamp, last_candle_time, timestamp-last_candle_time, round(1.5+(timestamp-last_candle_time)/timeframe_secs))
        if '"code":-1130' in str(ex):
            watch_list.remove(symbol)
            print(f'{symbol} is removed from watch_list')
            logger.debug(f'{symbol} is removed from watch_list')

async def set_leverage(exchange, symbol, leverage):
    global all_symbols
    try:
        ex_symbol = exchange_symbol(symbol)
        if config.automaxLeverage == "on":
            logger.debug(f'{symbol} {ex_symbol} {leverage}')
            await exchange.set_leverage(leverage, ex_symbol)
        else:
            leverage = config.Leverage
            if symbol in symbols_setting.index:
                leverage = int(symbols_setting.loc[symbol]['leverage'])
            await exchange.set_leverage(leverage, ex_symbol)

        # เก็บค่า leverage ไว้ใน all_symbols เพื่อเอาไปใช้ต่อที่อื่น
        all_symbols[symbol]['leverage'] = leverage
    except Exception as ex:
        logger.debug(f'{symbol} {ex_symbol} {type(ex).__name__} {str(ex)}')
        if config.automaxLeverage == "on":
            new_leverage = config.Leverage
        else:
            new_leverage = 5
        if type(ex).__name__ == 'ExchangeError' and '-4300' in str(ex):
            new_leverage = config.Leverage
        print(ex_symbol, f'found leverage {leverage} error, Bot will set leverage = {new_leverage}')
        logger.info(f'{symbol} {ex_symbol} found leverage {leverage} error, Bot will set leverage = {new_leverage}')
        try:
            await exchange.set_leverage(new_leverage, ex_symbol)

            all_symbols[symbol]['leverage'] = new_leverage
        except Exception as ex:
            # print(type(ex).__name__, str(ex))
            print(ex_symbol, f'can not set leverage')
            logger.info(f'{ex_symbol} can not set leverage')
            all_symbols[symbol]['leverage'] = 1

async def fetch_ohlcv_trade(exchange, symbol, timeframe, limit=1, timestamp=0):
    await fetch_ohlcv(exchange, symbol, timeframe, limit, timestamp)
    await gather( go_trade(exchange, symbol) )

# order management zone --------------------------------------------------------
def new_order_history(symbol):
    global orders_history
    orders_history[symbol] = {
        'timestamp': 0,
        'positions': {},
        'orders': {},
        'orders_open': {}, 
        'win': 0, 
        'loss': 0, 
        'trade': 1,
        'last_loss': 0
    }
def open_order_history(symbol, positionSide:str, isTradeCount=True):
    global orders_history
    if symbol not in orders_history.keys():
        new_order_history(symbol)
    position = {}
    position['info'] = {}
    if positionSide == 'long' or config.isHedgeTrade == False:
        orders_history[symbol]['positions'] = {}
        orders_history[symbol]['orders'] = {}
        orders_history[symbol]['orders_open'] = {}
    orders_history[symbol]['positions'][positionSide] = position
    orders_history[symbol]['positions'][positionSide]['status'] = 'open'
    if isTradeCount:
        orders_history[symbol]['trade'] = orders_history[symbol]['trade'] + 1
def close_order_history(symbol, positionSide:str):
    global orders_history
    if symbol in orders_history.keys():
        new_order_history(symbol)
    if positionSide in orders_history[symbol]['positions'].keys():
        orders_history[symbol]['positions'][positionSide]['status'] = 'close'
    positions = all_positions[all_positions['symbol'] == symbol]
    positionInfo = positions.iloc[0]
    logger.debug(f'{symbol} close_order_history\n{positionInfo}')
    profit = 0
    if len(positions) > 0 and float(positionInfo["unrealizedProfit"]) != 0:
        profit = float(positionInfo["unrealizedProfit"])
    if profit > 0:
        orders_history[symbol]['win'] = orders_history[symbol]['win'] + 1
        orders_history[symbol]['last_loss'] = 0
    elif profit < 0:
        orders_history[symbol]['loss'] = orders_history[symbol]['loss'] + 1
        orders_history[symbol]['last_loss'] = orders_history[symbol]['last_loss'] + 1
def update_order_history(symbol, orderType:str, order):
    global orders_history
    if symbol not in orders_history.keys():
        new_order_history(symbol)
    try:
        positionSide = str(order['info']['positionSide']).lower()
        if positionSide not in orders_history[symbol]['positions'].keys():
            position = {}
            position['info'] = {}
            orders_history[symbol]['positions'][positionSide] = position
        elif 'info' not in orders_history[symbol]['positions'][positionSide].keys():
            orders_history[symbol]['positions'][positionSide]['info'] = {}
        
        position_info = orders_history[symbol]['positions'][positionSide]['info']
        if orderType.lower() == 'long' or orderType.lower() == 'short':
            position_info['side'] = order['side']
            position_info['clientOrderId'] = order['clientOrderId']
            clientId_tokens = str(position_info['clientOrderId']).split('_')
            orders_history[symbol]['timestamp'] = int(clientId_tokens[2])
            position_info['price'] = order['price']
            position_info['amount'] = order['amount']
            position_info['cost'] = order['cost']
        elif orderType.lower() == 'tp':
            position_info['tp_price'] = order['stopPrice']
            position_info['tp_amount'] = order['amount']
        elif orderType.lower() == 'sl':
            position_info['sl_price'] = order['stopPrice']
            position_info['sl_amount'] = order['amount']
        elif orderType.lower() == 'tl':
            position_info['tl_activatePrice'] = float(order['info']['activatePrice'])
            position_info['tl_amount'] = order['amount']
            position_info['tl_callback'] = float(order['info']['priceRate'])
        elif orderType.lower() == 'close':
            position_info['close_price'] = order['price']
            position_info['close_amount'] = order['amount']
        orders_history[symbol]['positions'][positionSide]['info'] = position_info
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception(f'update_order_history')
        pass
async def update_open_orders(exchange, symbol):
    global orders_history
    if symbol not in orders_history.keys():
        new_order_history(symbol)
    open_orders = await exchange.fetch_open_orders(symbol)
    # logger.debug(f'{symbol} update_open_orders {open_orders}')
    order_count = 0
    orders = {}
    orders_open = {}
    for order in open_orders:
        order_count += 1
        positionSide = str(order['info']['positionSide']).lower()
        if positionSide not in orders_history[symbol]['positions'].keys():
            orders_history[symbol]['positions'][positionSide] = {}
        orders_history[symbol]['positions'][positionSide]['status'] = 'open'
        if positionSide not in orders.keys():
            orders[positionSide] = []
            orders_open[positionSide] = ['..','..','..']
        clientOrderId = str(order['clientOrderId'])
        order_info = { 
            'clientOrderId': clientOrderId,
            'type': order['type'],
            'stopPrice': order['stopPrice'],
            'amount': order['amount'],
        }
        if order['type'] == 'trailing_stop_market':
            orders_open[positionSide][2] = 'TL'
        elif order['type'] == 'stop' or order['type'] == 'stop_market':
            orders_open[positionSide][1] = 'SL'
        elif order['type'] == 'take_profit_market':
            orders_open[positionSide][0] = 'TP'
        orders[positionSide].append(order_info)
    orders_history[symbol]['orders'] = orders
    orders_history[symbol]['orders_open'] = orders_open

    # # re create order
    # for p_side in orders_history[symbol]['positions']:
    #     if p_side in ['long','short'] and order_count == 0:
    #         if config.TPSL_Mode == 'on':
    #             orders[p_side] = []
    #             orders_open[p_side] = ['..','..','..']
    #             p_info = orders_history[symbol]['positions'][p_side]['info']
    #             closeRate = p_info['tp_amount']/p_info['amount']*100.0
    #             if p_side == 'long':
    #                 long_TP(exchange, symbol, p_info['amount'], p_info['"tp_price"'], closeRate, False)
    #                 orders_history[symbol]['positions']['orders_open'][p_side][0] = 'tp'
    #                 pass
    #             elif p_side == 'short':
    #                 short_TP(exchange, symbol, p_info['amount'], p_info['"tp_price"'], closeRate, False)
    #                 orders_history[symbol]['positions']['orders_open'][p_side][0] = 'tp'
    #                 pass

def save_orders_history_csv(filename):
    oh_json = [{
        'symbol':symbol,
        'win':orders_history[symbol]['win'],
        'loss':orders_history[symbol]['loss'],
        'trade':orders_history[symbol]['trade']
    } for symbol in orders_history.keys()]
    oh_df = pd.DataFrame(oh_json)
    oh_df.to_csv(filename, index=False)
def save_orders_history_json(filename):
    with open(filename,"w", encoding='utf8') as json_file:
        json_string = json.dumps(orders_history, indent=2, ensure_ascii=False).encode('utf8')
        json_file.write(json_string.decode())
def load_orders_history_json(filename):
    global orders_history
    if os.path.exists(filename):
        with open(filename,"r", encoding='utf8') as json_file:
            orders_history = json.load(json_file)

# trading zone -----------------------------------------------------------------
def genClientOrderId(symbol, code, share_timestamp=False):
    # global orders_history
    # order id len <= 32 chars
    # format: {botname}_{tf}_{timestamp}_{magic number}
    # sample: ema_3m_1674903982845_99999
    if share_timestamp and symbol in orders_history.keys():
        tmst = orders_history[symbol]['timestamp']
    else:
        tmst = int(round(datetime.now().timestamp()*1000))
    gen_order_id = f"ema_{code}_{tmst}_{config.magic_number}"
    gen_order_id = gen_order_id[0:32]
    # logger.debug(gen_order_id)
    return gen_order_id
async def long_enter(exchange, symbol, amount, tf=config.timeframe):
    params={
        "newClientOrderId": genClientOrderId(symbol, tf),
    }
    positionSide = "BOTH"
    if is_positionside_dual:
        positionSide = "LONG"
    params["positionSide"] = positionSide
    order = await exchange.create_market_order(symbol, 'buy', amount, params=params)
    # print("Status : LONG ENTERING PROCESSING...")
    logger.debug(f'{symbol} long_enter {str(order)}')
    open_order_history(symbol, 'long')
    update_order_history(symbol, 'long', order)
    await sleep(1)
    return
#-------------------------------------------------------------------------------
async def long_close(exchange, symbol, positionAmt, tf=config.timeframe):
    params={
        "newClientOrderId": genClientOrderId(symbol, 'l-cl', True),
    }
    if is_positionside_dual:
        params["positionSide"] = "LONG"
    else:
        params["positionSide"] = "BOTH"
        params["reduceOnly"] = True
    order = await exchange.create_market_order(symbol, 'sell', positionAmt, params=params)
    logger.debug(f'{symbol} long_close {str(order)}')
    close_order_history(symbol, 'long')
    update_order_history(symbol, 'close', order)
    await cancel_order(exchange, symbol, 'long')
    return
#-------------------------------------------------------------------------------
async def short_enter(exchange, symbol, amount, tf=config.timeframe):
    params={
        "newClientOrderId": genClientOrderId(symbol, tf),
    }
    positionSide = "BOTH"
    if is_positionside_dual:
        positionSide = "SHORT"
    params["positionSide"] = positionSide
    order = await exchange.create_market_order(symbol, 'sell', amount, params=params)
    # print("Status : SHORT ENTERING PROCESSING...")
    logger.debug(f'{symbol} short_enter {str(order)}')
    open_order_history(symbol, 'short')
    update_order_history(symbol, 'short', order)
    await sleep(1)
    return
#-------------------------------------------------------------------------------
async def short_close(exchange, symbol, positionAmt, tf=config.timeframe):
    params={
        "newClientOrderId": genClientOrderId(symbol, 's-cl', True),
    }
    if is_positionside_dual:
        params["positionSide"] = "SHORT"
    else:
        params["positionSide"] = "BOTH"
        params["reduceOnly"] = True
    order = await exchange.create_market_order(symbol, 'buy', (positionAmt*-1), params=params)
    logger.debug(f'{symbol} short_close {str(order)}')
    close_order_history(symbol, 'short')
    update_order_history(symbol, 'close', order)
    await cancel_order(exchange, symbol, 'short')
    return
#-------------------------------------------------------------------------------
async def cancel_order(exchange, symbol, positionSide:str=None):
    try:
        await sleep(1)
        if positionSide == 'all':
            order = await exchange.cancel_all_orders(symbol, params={'conditionalOrdersOnly':False})
            logger.debug(f'{symbol} cancel_order {positionSide} {str(order)}')
        elif positionSide in ['long', 'short']:
            side = 'buy' if positionSide == 'short' else 'sell'
            open_orders = await exchange.fetch_open_orders(symbol)
            loops = [exchange.cancel_order(x['id'], x['symbol']) for x in open_orders if x['side'] == side]
            orders = await gather(*loops)
            logger.debug(f'{symbol} cancel_order {positionSide} {str(orders)}')
    except Exception as ex:
        print(type(ex).__name__, symbol, str(ex))
        logger.exception(f'cancel_order {symbol}')
        pass
    return
#-------------------------------------------------------------------------------
async def long_TPSL(exchange, symbol, amount, PriceEntry, pricetp, pricesl, closeRate):
    logger.debug(f'{symbol} long_TPSL PriceEntry:{PriceEntry}')
    if pricetp > 0.0:
        await long_TP(exchange, symbol, amount, pricetp, closeRate)
    if pricesl > 0.0:
        await long_SL(exchange, symbol, amount, pricesl)
    return
async def long_TP(exchange, symbol, amount, pricetp, closeRate, newOrder=True):
    closetp = closeRate/100.0
    closeamt = amount_to_precision(symbol, amount*closetp)
    if closeamt == 0.0:
        closeamt = amount
    logger.debug(f'{symbol} long_TP amount:{amount}, pricetp:{pricetp}, closetp:{closetp}, closeRate:{closeRate}, closeamt:{closeamt}')
    params = {
        "newClientOrderId": genClientOrderId(symbol, 'l-tp', True),
    }
    if is_positionside_dual:
        params["positionSide"] = "LONG"
    else:
        params["positionSide"] = "BOTH"
    params['stopPrice'] = pricetp
    params['triggerPrice'] = pricetp
    order = await exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'sell', closeamt, pricetp, params=params)
    logger.debug(f'{symbol} long_TP {str(order)}')
    if newOrder:
        update_order_history(symbol, 'tp', order)
    await sleep(1)
    return
async def long_SL(exchange, symbol, amount, pricesl, newOrder=True):
    logger.debug(f'{symbol} long_SL amount:{amount}, pricesl:{pricesl}')
    params = {
        "newClientOrderId": genClientOrderId(symbol, 'l-sl', True),
    }
    if is_positionside_dual:
        params["positionSide"] = "LONG"
        SL_CMD = 'STOP'
    else:
        params["positionSide"] = "BOTH"
        SL_CMD = 'STOP_MARKET'
    params['stopPrice'] = pricesl
    params['triggerPrice'] = pricesl
    if not is_positionside_dual:
        params["reduceOnly"] = True
    order = await exchange.create_order(symbol, SL_CMD, 'sell', amount, pricesl, params=params)
    logger.debug(f'{symbol} long_SL {str(order)}')
    if newOrder:
        update_order_history(symbol, 'sl', order)
    await sleep(1)
    return
#-------------------------------------------------------------------------------
async def short_TPSL(exchange, symbol, amount, PriceEntry, pricetp, pricesl, closeRate):
    logger.debug(f'{symbol} short_TPSL PriceEntry:{PriceEntry}')
    await short_TP(exchange, symbol, amount, pricetp, closeRate)
    await short_SL(exchange, symbol, amount, pricesl)
    return
async def short_TP(exchange, symbol, amount, pricetp, closeRate, newOrder=True):
    closetp = closeRate/100.0
    closeamt = amount_to_precision(symbol, amount*closetp)
    if closeamt == 0.0:
        closeamt = amount
    logger.debug(f'{symbol} short_TP amount:{amount}, pricetp:{pricetp}, closetp:{closetp}, closeRate:{closeRate}, closeamt:{closeamt}')
    params = {
        "newClientOrderId": genClientOrderId(symbol, 's-tp', True),
    }
    if is_positionside_dual:
        params["positionSide"] = "SHORT"
    else:
        params["positionSide"] = "BOTH"
    params['stopPrice'] = pricetp
    params['triggerPrice'] = pricetp
    order = await exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'buy', closeamt, pricetp, params=params)
    logger.debug(f'{symbol} short_TP {str(order)}')
    if newOrder:
        update_order_history(symbol, 'tp', order)
    await sleep(1)
    return
async def short_SL(exchange, symbol, amount, pricesl, newOrder=True):
    logger.debug(f'{symbol} short_TP amount:{amount}, pricesl:{pricesl}')
    params = {
        "newClientOrderId": genClientOrderId(symbol, 's-sl', True),
    }
    if is_positionside_dual:
        params["positionSide"] = "SHORT"
        SL_CMD = 'STOP'
    else:
        params["positionSide"] = "BOTH"
        SL_CMD = 'STOP_MARKET'
    params['stopPrice'] = pricesl
    params['triggerPrice'] = pricesl
    if not is_positionside_dual:
        params["reduceOnly"] = True
    order = await exchange.create_order(symbol, SL_CMD, 'buy', amount, pricesl, params=params)        
    logger.debug(f'{symbol} short_TP {str(order)}')
    if newOrder:
        update_order_history(symbol, 'sl', order)
    await sleep(1)
    return
#-------------------------------------------------------------------------------
# BUY: the lowest price after order placed <= activationPrice, 
#      and the latest price >= the lowest price * (1 + callbackRate)
# BUY: activationPrice should be smaller than latest price.
# SELL: the highest price after order placed >= activationPrice, 
#       and the latest price <= the highest price * (1 - callbackRate)
# SELL: activationPrice should be larger than latest price.
#-------------------------------------------------------------------------------
async def long_TLSTOP(exchange, symbol, amount, priceTL, callbackRate):
    params = {
        "newClientOrderId": genClientOrderId(symbol, 'l-tl', True),
        'callbackRate': callbackRate, 
    }
    if is_positionside_dual:
        params["positionSide"] = "LONG"
    else:
        params["positionSide"] = "BOTH"
        params["reduceOnly"] = True
    if priceTL > 0:
        params['activationPrice'] = priceTL
    logger.debug(f'{symbol} amount:{amount}, activationPrice:{priceTL}, callbackRate:{callbackRate}')
    order = await exchange.create_order(symbol, 'TRAILING_STOP_MARKET', 'sell', amount, params=params)
    logger.debug(f'{symbol} long_TLSTOP {str(order)}')
    update_order_history(symbol, 'tl', order)
    activatePrice = float(order['info']['activatePrice'])
    logger.debug(f'{symbol} amount:{amount}, activationPrice:{priceTL}, activatePrice:{activatePrice}, callbackRate:{callbackRate}')
    await sleep(1)
    return activatePrice
#-------------------------------------------------------------------------------
async def short_TLSTOP(exchange, symbol, amount, priceTL, callbackRate):
    params = {
        "newClientOrderId": genClientOrderId(symbol, 's-tl', True),
        'callbackRate': callbackRate, 
    }
    if is_positionside_dual:
        params["positionSide"] = "SHORT"
    else:
        params["positionSide"] = "BOTH"
        params["reduceOnly"] = True
    if priceTL > 0:
        params['activationPrice'] = priceTL
    logger.debug(f'{symbol} amount:{amount}, activationPrice:{priceTL}, callbackRate: {callbackRate}')
    order = await exchange.create_order(symbol, 'TRAILING_STOP_MARKET', 'buy', amount, params=params)
    logger.debug(f'{symbol} short_TLSTOP {str(order)}')
    update_order_history(symbol, 'tl', order)
    activatePrice = float(order['info']['activatePrice'])
    logger.debug(f'{symbol} amount:{amount}, activationPrice:{priceTL}, activatePrice:{activatePrice}, callbackRate:{callbackRate}')
    await sleep(1)
    return activatePrice
#-------------------------------------------------------------------------------
async def cal_amount(exchange, symbol, leverage, costType, costAmount, closePrice, chkLastPrice):
    # คำนวนจำนวนเหรียญที่ใช้เปิดออเดอร์
    priceEntry = float(closePrice)
    # minAmount = float(all_symbols[symbol]['minAmount'])
    # minCost = float(all_symbols[symbol]['minCost'])
    if chkLastPrice:
        try:
            ticker = await exchange.fetch_ticker(symbol)
            logger.debug(f'{symbol}:ticker\n{ticker}')
            priceEntry = float(ticker['last'])
        except Exception as ex:
            print(type(ex).__name__, str(ex))
    if costType=='#':
        amount = costAmount / priceEntry
    elif costType=='$':
        amount = costAmount * float(leverage) / priceEntry
    # elif costType=='M':
    #     # amount = priceEntry * minAmount / float(leverage) * 1.1
    #     amount =  minCost / float(leverage) / priceEntry * 1.1 
    else:
        # amount = (float(balance_entry)/100) * costAmount * float(leverage) / priceEntry
        amount = (float(balalce_total)/100) * costAmount * float(leverage) / priceEntry

    p_amount = amount_to_precision(symbol, amount)
    amount_precision = all_symbols[symbol]['amount_precision']

    logger.info(f'{symbol} lev:{leverage} close:{closePrice} last:{priceEntry} amt:{amount} p_amt:{p_amount} p:{amount_precision}')

    return (priceEntry, p_amount)

def crossover(tupleA, tupleB):
    return (tupleA[0] < tupleB[0] and tupleA[1] > tupleB[1])

async def go_trade(exchange, symbol, chkLastPrice=True):
    global all_positions, balance_entry, count_trade, count_trade_long, count_trade_short, total_margin

    # delay เพื่อให้กระจายการ trade ของ symbol มากขึ้น
    delay = randint(5,10)
    # จัดลำดับการ trade symbol
    if symbol in orders_history.keys():
        winRate = orders_history[symbol]['win']/orders_history[symbol]['trade']
        if winRate > 0.5:
            delay = 0
        elif winRate == 0.5:
             delay = 4
    await sleep(delay)

    # อ่านข้อมูลแท่งเทียนที่เก็บไว้ใน all_candles
    if symbol in all_candles.keys() and len(all_candles[symbol]) >= CANDLE_SAVE:
        df = all_candles[symbol]
    else:
        print(f'not found candles for {symbol}')
        return
    # อ่านข้อมูล leverage ที่เก็บไว้ใน all_symbols
    if symbol in all_symbols.keys():
        leverage = all_symbols[symbol]['leverage']
    else:
        print(f'not found leverage for {symbol}')
        return

    marginType = all_symbols[symbol]['quote']

    hasLongPosition = False
    hasShortPosition = False
    positionAmt = 0.0
    unrealizedProfit = 0.0
    
    positionInfo = all_positions.loc[all_positions['symbol']==symbol]

    if not positionInfo.empty and float(positionInfo.iloc[-1]["positionAmt"]) != 0:
        positionAmt = float(positionInfo.iloc[-1]["positionAmt"])
        unrealizedProfit = float(positionInfo.iloc[-1]["unrealizedProfit"])

    hasLongPosition = (positionAmt > 0)
    hasShortPosition = (positionAmt < 0)

    # print(countTrade, positionAmt, hasLongPosition, hasShortPosition, amount)

    # if positionAmt == 0 and symbol in orders_history.keys():
    #     await cancel_order(exchange, symbol)

    try:
        signalIdx = config.SignalIndex
        tradeMode = config.Trade_Mode
        TPSLMode = config.TPSL_Mode
        trailingStopMode = config.Trailing_Stop_Mode
        costType = config.CostType
        costAmount = config.CostAmount
        adxIn = config.ADXIn
        positionLong = config.PositionLong
        positionValueLong = config.PositionValueLong
        positionShort = config.PositionShort
        positionValueShort = config.PositionValueShort
        exitLong = config.ExitLong
        exitValueLong = config.ExitValueLong
        exitShort = config.ExitShort
        exitValueShort = config.ExitValueShort
        stoValueLong = config.STOEnterLong
        stoExitLong = config.STOExitLong
        stoValueShort = config.STOEnterShort
        stoExitShort = config.STOExitShort
        if symbol in symbols_setting.index:
            signalIdx = int(symbols_setting.loc[symbol]['signal_index'])
            tradeMode = symbols_setting.loc[symbol]['trade_mode']
            TPSLMode = symbols_setting.loc[symbol]['tpsl_mode']
            trailingStopMode = symbols_setting.loc[symbol]['trailing_stop_mode']
            costType = symbols_setting.loc[symbol]['cost_type']
            costAmount = float(symbols_setting.loc[symbol]['cost_amount'])
            adxIn = int(symbols_setting.loc[symbol]['adx_in'])
            positionLong = symbols_setting.loc[symbol]['position_long']
            positionValueLong = int(symbols_setting.loc[symbol]['position_value_long'])
            positionShort = symbols_setting.loc[symbol]['position_short']
            positionValueShort = int(symbols_setting.loc[symbol]['position_value_short'])
            exitLong = symbols_setting.loc[symbol]['exit_long']
            exitValueLong = int(symbols_setting.loc[symbol]['exit_value_long'])
            exitShort = symbols_setting.loc[symbol]['exit_short']
            exitValueShort = int(symbols_setting.loc[symbol]['exit_value_short'])
            stoValueLong = int(symbols_setting.loc[symbol]['sto_enter_long'])
            stoExitLong = int(symbols_setting.loc[symbol]['sto_exit_long'])
            stoValueShort = int(symbols_setting.loc[symbol]['sto_enter_short'])
            stoExitShort = int(symbols_setting.loc[symbol]['sto_exit_short'])

        kwargs = dict(
            ADXIn=adxIn,
            RSIhi=positionValueLong,
            RSIlo=positionValueShort,
            STOhi=stoValueLong,
            STOlo=stoValueShort
        )

        rsi = (df.iloc[signalIdx-1]['RSI'], df.iloc[signalIdx]['RSI'])
        adxLast = df.iloc[signalIdx]['ADX']
        # close = (df.iloc[signalIdx-1]['close'], df.iloc[signalIdx]['close'])
        stoK = (df.iloc[signalIdx-1]['STOCHk'], df.iloc[signalIdx]['STOCHk'])
        stoD = (df.iloc[signalIdx-1]['STOCHd'], df.iloc[signalIdx]['STOCHd'])

        # logger.debug(f'{symbol} -> rsi:{rsi} adx:{adxLast} stoK:{stoK} stoD:{stoD}')

        # Long Enter
        isLongEnter = adxLast > adxIn and (
            (positionLong == 'up' and rsi[0] < positionValueLong and rsi[1] > positionValueLong) or
            (positionLong == 'down' and rsi[0] > positionValueLong and rsi[1] < positionValueLong)
            )
        
        # Long Exit
        isLongExit = (exitLong == 'up' and rsi[1] > exitValueLong) or (exitLong == 'down' and rsi[1] < exitValueLong)        

        # Short Enter
        isShortEnter = adxLast > adxIn and (
            (positionShort == 'up' and rsi[0] > positionValueShort and rsi[1] < positionValueShort) or
            (positionShort == 'down' and rsi[0] < positionValueShort and rsi[1] > positionValueShort)
            )

        # Short Exit
        isShortExit = (exitShort == 'up' and rsi[1] > exitValueShort) or (exitShort == 'down' and rsi[1] < exitValueShort)
        
        if not config.isADXRSIEnterMode:
            isLongEnter = False
            isShortEnter = False

        if not config.isADXRSIExitMode:
            isLongExit = False
            isShortExit = False

        # logger.debug(f'{symbol} -> isLongEnter:{isLongEnter} isShortEnter:{isShortEnter} isLongExit:{isLongExit} isShortExit:{isShortExit}')

        co_STO = stoK[0] < stoD[0] and stoK[1] > stoD[1]
        cu_STO = stoK[0] > stoD[0] and stoK[1] < stoD[1]
        isSTOLongEnter = co_STO and stoD[1] <= stoValueLong
        isSTOShortEnter = cu_STO and stoD[1] >= stoValueShort
        isSTOLongExit = stoD[1] >= stoExitLong
        isSTOShortExit = stoD[1] <= stoExitShort

        if config.isConfirmSMAMode:
            close = df.iloc[signalIdx]['close']
            open = df.iloc[signalIdx]['open']
            sma_lo = df.iloc[signalIdx]['SMAlo']
            sma_hi = df.iloc[signalIdx]['SMAhi']
            # logger.debug(f'{symbol} -> close:{close} open:{open} sma_lo:{sma_lo} sma_hi:{sma_hi}')  
            isSTOLongEnter = co_STO and stoD[1] <= stoValueLong and close < sma_lo and open < sma_lo 
            isSTOShortEnter = cu_STO and stoD[1] >= stoValueShort and close > sma_hi and open > sma_hi

        # logger.debug(f'{symbol} -> isSTOLongEnter:{isSTOLongEnter} isSTOShortEnter:{isSTOShortEnter}')

        if config.isADXRSIEnterMode and config.isSTOOn:
            isLongEnter = isLongEnter and isSTOLongEnter
            isShortEnter = isShortEnter and isSTOShortEnter
        elif config.isSTOOn:
            isLongEnter = isSTOLongEnter
            isShortEnter = isSTOShortEnter

        if config.isADXRSIExitMode and config.isSTOOn:
            isLongExit = isLongExit or isSTOShortEnter
            isShortExit = isShortExit or isSTOLongEnter
        elif config.isSTOOn:
            isLongExit = isSTOLongExit
            isShortExit = isSTOShortExit

        if config.isHedgeTrade and (isLongEnter or isShortEnter):
            if is_positionside_dual == True:
                isShortEnter = True
                isLongEnter = True
                print(f"[{symbol}] Hedge Mode No")
                logger.info(f'{symbol} -> Hedge Mode No')
            else:
                print(f"[{symbol}] Hedge Mode Off")
                logger.info(f'{symbol} -> Hedge Mode Off')

        # print(symbol, isLongEnter, isShortEnter, rsi, adxLast, stoK, stoD)
        # logger.debug(f'{symbol} -> isLongExit:{isLongExit} isShortExit:{isShortExit}')

        closePrice = df.iloc[-1]["close"]

        if tradeMode == 'on' and isShortExit == True and hasShortPosition == True:
            count_trade_short = count_trade_short - 1 if count_trade_short > 0 else 0
            count_trade = count_trade_long + count_trade_short
            try:
                await short_close(exchange, symbol, positionAmt)
                hasShortPosition = False
                print(f"[{symbol}] สถานะ : Short Exit processing...")
                # await cancel_order(exchange, symbol, 'short')
                # line_notify(f'{symbol}\nสถานะ : Short RSI Exit\n{round(rsi[1],1)}')
                gather( line_chart(symbol, df, f'{symbol}\nสถานะ : Short Exit\nราคาปิด : {closePrice}\nกำไร : {unrealizedProfit}', 'SHORT EXIT', **kwargs) )
            except Exception as ex:
                print(type(ex).__name__, symbol, str(ex))
                logger.exception(f'go_trade {symbol} short exit')
        elif tradeMode == 'on' and isLongExit == True and hasLongPosition == True:
            count_trade_long = count_trade_long - 1 if count_trade_long > 0 else 0
            count_trade = count_trade_long + count_trade_short
            try:
                await long_close(exchange, symbol, positionAmt)
                hasLongPosition = False
                print(f"[{symbol}] สถานะ : Long Exit processing...")
                # await cancel_order(exchange, symbol, 'long')
                # line_notify(f'{symbol}\nสถานะ : Long RSI Exit\n{round(rsi[1],1)}')
                # \nADX : {round(adxLast,1)}\nRSI : {round(rsi[1],1)}\nSTOk : {round(stoK[1],1)}\nราคา : {priceEntry}
                gather( line_chart(symbol, df, f'{symbol}\nสถานะ : Long Exit\nราคาปิด : {closePrice}\nกำไร : {unrealizedProfit}', 'LONG EXIT', **kwargs) )
            except Exception as ex:
                print(type(ex).__name__, symbol, str(ex))
                logger.exception(f'go_trade {symbol} short exit')
        # elif tradeMode == 'on' and (isLongEnter or isShortEnter):
        #     try:
        #         await cancel_order(exchange, symbol, 'all')
        #     except Exception as ex:
        #         print(type(ex).__name__, symbol, str(ex))
        #         logger.exception(f'go_trade {symbol} cancel order')

        isRiskLimit = (config.risk_limit > 0) and (total_risk[marginType] > config.risk_limit)

        if isRiskLimit:

            print(f"[{symbol}] RiskLimit {total_risk[marginType]:,.2f}% skipping...")
            logger.info(f'{symbol} -> RiskLimit {total_risk[marginType]:,.2f}% skipping...')

        else:

            # logger.debug(f'{symbol} -> isLongEnter:{isLongEnter} isShortEnter:{isShortEnter}')

            notify_msg = []
            notify_msg.append(symbol)

            if isLongEnter == True and config.Long == 'on' and hasLongPosition == False:
                TPLong = config.TP_Long
                TPCloseLong = config.TP_Close_Long
                SLLong = config.SL_Long
                callbackLong = config.Callback_Long
                activeTLLong = config.Active_TL_Long
                if symbol in symbols_setting.index:
                    TPLong = float(symbols_setting.loc[symbol]['tp_long'])
                    TPCloseLong = float(symbols_setting.loc[symbol]['tp_close_long'])
                    SLLong = float(symbols_setting.loc[symbol]['sl_long'])
                    callbackLong = float(symbols_setting.loc[symbol]['callback_long'])
                    activeTLLong = float(symbols_setting.loc[symbol]['active_tl_long'])

                print(f'{symbol:12} LONG')
                fibo_data = cal_minmax_fibo(symbol, df, 'LONG', closePrice)
                if tradeMode == 'on' and balance_entry[marginType] > config.Not_Trade \
                    and (config.limit_Trade > count_trade or config.limit_Trade_Long > count_trade_long) :
                    count_trade_long = count_trade_long + 1
                    count_trade = count_trade_long + count_trade_short
                    (priceEntry, amount) = await cal_amount(exchange, symbol, leverage, costType, costAmount, closePrice, chkLastPrice)
                    if amount <= 0.0:
                        print(f"[{symbol}] Status : NOT TRADE LONG, Amount <= 0.0")
                    elif amount*priceEntry < 5.0:
                        print(f"[{symbol}] Status : NOT TRADE LONG, Cost < 5.0")
                    else:
                        marginAmount = (amount * priceEntry / leverage)
                        availableBalance = balance_entry[marginType] - marginAmount
                        totalMargin = total_margin[marginType] + marginAmount
                        # calculate risk before open new opsition
                        risk = 0
                        if availableBalance + totalMargin > 0:
                            risk = (config.maint_margin_ratio * totalMargin) / (availableBalance + totalMargin) * 100
                        if config.risk_limit > 0 and risk > config.risk_limit:
                            print(f"[{symbol}] Status : NOT TRADE LONG, RiskLimit {risk:,.2f}%")
                        else:
                            # ปรับปรุงค่า balance_entry
                            balance_entry[marginType] = availableBalance
                            total_margin[marginType] = totalMargin
                            print('balance_entry', balance_entry[marginType])
                            await cancel_order(exchange, symbol, 'long')
                            await long_enter(exchange, symbol, amount)
                            print(f"[{symbol}] Status : LONG ENTERING PROCESSING...")
                            # await cancel_order(exchange, symbol)
                            notify_msg.append(f'สถานะ : Long\nราคา : {priceEntry}')

                            logger.debug(f'{symbol} LONG\n{df.tail(3)}')

                            closeRate = 100.0
                            priceTL = 0.0
                            if TPSLMode == 'on':
                                notify_msg.append(f'# TPSL')
                                if config.TP_PNL_Long > 0:
                                    closeRate = config.TP_PNL_Close_Long
                                    if config.is_percent_mode:
                                        pricetp = price_to_precision(symbol, priceEntry + (costAmount * (config.TP_PNL_Long / 100.0) / amount))
                                        fibo_data['tp_txt'] = f'TP PNL: {config.TP_PNL_Long:.2f}% @{pricetp}'
                                    else:
                                        pricetp = price_to_precision(symbol, priceEntry + (config.TP_PNL_Long / amount))
                                        fibo_data['tp_txt'] = f'TP PNL: {config.TP_PNL_Long:.2f}$ @{pricetp}'
                                    fibo_data['tp'] = pricetp
                                    if config.CB_AUTO_MODE == 1:
                                        fibo_data['callback_rate'] = cal_callback_rate(symbol, priceEntry, pricetp)
                                    if config.Active_TL_PNL_Long > 0:
                                        if config.is_percent_mode:
                                            priceTL = price_to_precision(symbol, priceEntry + (costAmount * (config.Active_TL_PNL_Long / 100.0) / amount))
                                        else:
                                            priceTL = price_to_precision(symbol, priceEntry + (config.Active_TL_PNL_Long / amount))
                                    callbackLong = config.Callback_PNL_Long
                                else:
                                    closeRate = TPCloseLong
                                    if TPLong > 0:
                                        pricetp = price_to_precision(symbol, priceEntry + (priceEntry * (TPLong / 100.0)))
                                        fibo_data['tp_txt'] = f'TP: {TPLong:.2f}% @{pricetp}'
                                        fibo_data['tp'] = pricetp
                                    elif TPLong < 0:
                                        pricetp = 0.0
                                        fibo_data['tp_txt'] = f'TP: None'
                                        fibo_data['tp'] = pricetp
                                    else:
                                        pricetp = fibo_data['tp']
                                        fibo_data['tp_txt'] = f'TP: (AUTO) @{pricetp}'
                                    if activeTLLong > 0:
                                        priceTL = price_to_precision(symbol, priceEntry + (priceEntry * (activeTLLong / 100.0)))
                                notify_msg.append(fibo_data['tp_txt'])
                                notify_msg.append(f'TP close: {closeRate:.2f}%')
                                if config.SL_PNL_Long > 0:
                                    if config.is_percent_mode:
                                        pricesl = price_to_precision(symbol, priceEntry - (costAmount * (config.SL_PNL_Long / 100.0) / amount))
                                        fibo_data['sl_txt'] = f'SL PNL: {config.SL_PNL_Long:.2f}% @{pricesl}'
                                    else:
                                        pricesl = price_to_precision(symbol, priceEntry - (config.SL_PNL_Long / amount))
                                        fibo_data['sl_txt'] = f'SL PNL: {config.SL_PNL_Long:.2f}$ @{pricesl}'
                                    fibo_data['sl'] = pricesl
                                    if config.CB_AUTO_MODE != 1:
                                        fibo_data['callback_rate'] = cal_callback_rate(symbol, priceEntry, pricesl)
                                elif SLLong > 0:
                                    pricesl = price_to_precision(symbol, priceEntry - (priceEntry * (SLLong / 100.0)))
                                    fibo_data['sl_txt'] = f'SL: {SLLong:.2f}% @{pricesl}'
                                    fibo_data['sl'] = pricesl
                                elif SLLong < 0:
                                    pricesl = 0.0
                                    fibo_data['sl_txt'] = f'SL: None'
                                    fibo_data['sl'] = pricesl
                                else:
                                    pricesl = fibo_data['sl']
                                    fibo_data['sl_txt'] = f'SL: (AUTO) @{pricesl}'
                                notify_msg.append(fibo_data['sl_txt'])

                                await long_TPSL(exchange, symbol, amount, priceEntry, pricetp, pricesl, closeRate)
                                print(f'[{symbol}] Set TP {pricetp} SL {pricesl}')

                            if trailingStopMode == 'on' and closeRate < 100.0:
                                notify_msg.append('# TrailingStop')
                                if priceTL == 0.0:
                                    # RR = 1
                                    activationPrice = price_to_precision(symbol, priceEntry + abs(priceEntry - pricesl))
                                else:
                                    activationPrice = priceTL

                                if callbackLong == 0.0:
                                    callbackLong = fibo_data['callback_rate']
                                    notify_msg.append(f'Call Back: (AUTO) {callbackLong:.2f}%')
                                else:
                                    notify_msg.append(f'Call Back: {callbackLong:.2f}%')

                                activatePrice = await long_TLSTOP(exchange, symbol, amount, activationPrice, callbackLong)
                                print(f'[{symbol}] Set Trailing Stop {activationPrice:.4f}')
                                # callbackLong_str = ','.join(['{:.2f}%'.format(cb) for cb in callbackLong])

                                if priceTL == 0.0:
                                    notify_msg.append(f'Active Price: (AUTO) @{activatePrice}')
                                elif config.TP_PNL_Long > 0:
                                    if config.is_percent_mode:
                                        notify_msg.append(f'Active Price PNL: {config.Active_TL_PNL_Long:.2f}% @{activatePrice}')
                                    else:
                                        notify_msg.append(f'Active Price PNL: {config.Active_TL_PNL_Long:.2f}$ @{activatePrice}')
                                elif activeTLLong > 0:
                                    notify_msg.append(f'Active Price: {activeTLLong:.2f}% @{activatePrice}')

                            gather( line_chart(symbol, df, '\n'.join(notify_msg), 'LONG', fibo_data, **kwargs) )

                elif tradeMode != 'on' :
                    fibo_data['tp_txt'] = 'TP'
                    fibo_data['sl_txt'] = 'SL'
                    gather( line_chart(symbol, df, f'{symbol}\nสถานะ : Long\nADX : {round(adxLast,1)}\nRSI : {round(rsi[1],1)}\nSTOk : {round(stoK[1],1)}', 'LONG', fibo_data, **kwargs) )

            notify_msg = []
            notify_msg.append(symbol)

            if isShortEnter == True and config.Short == 'on' and hasShortPosition == False:
                TPShort = config.TP_Short
                TPCloseShort = config.TP_Close_Short
                SLShort = config.SL_Short
                callbackShort = config.Callback_Short
                activeTLShort = config.Active_TL_Short
                if symbol in symbols_setting.index:
                    TPShort = float(symbols_setting.loc[symbol]['tp_short'])
                    TPCloseShort = float(symbols_setting.loc[symbol]['tp_close_short'])
                    SLShort = float(symbols_setting.loc[symbol]['sl_short'])
                    callbackShort = float(symbols_setting.loc[symbol]['callback_short'])
                    activeTLShort = float(symbols_setting.loc[symbol]['active_tl_short'])

                print(f'{symbol:12} SHORT')
                fibo_data = cal_minmax_fibo(symbol, df, 'SHORT', closePrice)
                if tradeMode == 'on' and balance_entry[marginType] > config.Not_Trade \
                    and (config.limit_Trade > count_trade or config.limit_Trade_Short > count_trade_short) :
                    count_trade_short = count_trade_short + 1
                    count_trade = count_trade_long + count_trade_short
                    (priceEntry, amount) = await cal_amount(exchange, symbol, leverage, costType, costAmount, closePrice, chkLastPrice)
                    if amount <= 0.0:
                        print(f"[{symbol}] Status : NOT TRADE SHORT, Amount <= 0.0")
                    elif amount*priceEntry < 5.0:
                        print(f"[{symbol}] Status : NOT TRADE LONG, Cost < 5.0")
                    else:
                        marginAmount = (amount * priceEntry / leverage)
                        availableBalance = balance_entry[marginType] - marginAmount
                        totalMargin = total_margin[marginType] + marginAmount
                        # calculate risk before open new opsition
                        risk = 0.0
                        if (availableBalance + totalMargin) > 0:
                            risk = (config.maint_margin_ratio * totalMargin) / (availableBalance + totalMargin) * 100
                        if config.risk_limit > 0 and risk > config.risk_limit:
                            print(f"[{symbol}] Status : NOT TRADE LONG, RiskLimit {risk:,.2f}%")
                        else:
                            # ปรับปรุงค่า balance_entry
                            balance_entry[marginType] = availableBalance
                            total_margin[marginType] = totalMargin
                            print('balance_entry', balance_entry[marginType])
                            await cancel_order(exchange, symbol, 'short')
                            await short_enter(exchange, symbol, amount)
                            print(f"[{symbol}] Status : SHORT ENTERING PROCESSING...")
                            # await cancel_order(exchange, symbol)
                            notify_msg.append(f'สถานะ : Short\nราคา : {priceEntry}')

                            logger.debug(f'{symbol} SHORT\n{df.tail(3)}')

                            closeRate = 100.0
                            priceTL = 0.0
                            if TPSLMode == 'on':
                                notify_msg.append(f'# TPSL')
                                if config.TP_PNL_Short > 0:
                                    closeRate = config.TP_PNL_Close_Short
                                    if config.is_percent_mode:
                                        pricetp = price_to_precision(symbol, priceEntry - (costAmount * (config.TP_PNL_Short / 100.0) / amount))
                                        fibo_data['tp_txt'] = f'TP PNL: {config.TP_PNL_Short:.2f}% @{pricetp}'
                                    else:
                                        pricetp = price_to_precision(symbol, priceEntry - (config.TP_PNL_Short / amount))
                                        fibo_data['tp_txt'] = f'TP PNL: {config.TP_PNL_Short:.2f}$ @{pricetp}'
                                    fibo_data['tp'] = pricetp
                                    if config.CB_AUTO_MODE == 1:
                                        fibo_data['callback_rate'] = cal_callback_rate(symbol, priceEntry, pricetp)
                                    if config.Active_TL_PNL_Short > 0:
                                        if config.is_percent_mode:
                                            priceTL = price_to_precision(symbol, priceEntry - (costAmount * (config.Active_TL_PNL_Short / 100.0) / amount))
                                        else:
                                            priceTL = price_to_precision(symbol, priceEntry - (config.Active_TL_PNL_Short / amount))
                                    callbackShort = config.Callback_PNL_Short
                                else:
                                    closeRate = TPCloseShort
                                    if TPShort > 0:
                                        pricetp = price_to_precision(symbol, priceEntry - (priceEntry * (TPShort / 100.0)))
                                        fibo_data['tp_txt'] = f'TP: {TPShort:.2f}% @{pricetp}'
                                        fibo_data['tp'] = pricetp
                                    elif TPShort < 0:
                                        pricetp = 0.0
                                        fibo_data['tp_txt'] = f'TP: None'
                                        fibo_data['tp'] = pricetp
                                    else:
                                        pricetp = fibo_data['tp']
                                        fibo_data['tp_txt'] = f'TP: (AUTO) @{pricetp}'
                                    if activeTLShort > 0:
                                        priceTL = price_to_precision(symbol, priceEntry - (priceEntry * (activeTLShort / 100.0)))
                                notify_msg.append(fibo_data['tp_txt'])
                                notify_msg.append(f'TP close: {closeRate:.2f}%')
                                if config.SL_PNL_Short > 0:
                                    if config.is_percent_mode:
                                        pricesl = price_to_precision(symbol, priceEntry + (costAmount * (config.SL_PNL_Short / 100.0) / amount))
                                        fibo_data['sl_txt'] = f'SL PNL: {config.SL_PNL_Short:.2f}% @{pricesl}'
                                    else:
                                        pricesl = price_to_precision(symbol, priceEntry + (config.SL_PNL_Short / amount))
                                        fibo_data['sl_txt'] = f'SL PNL: {config.SL_PNL_Short:.2f}$ @{pricesl}'
                                    fibo_data['sl'] = pricesl
                                    if config.CB_AUTO_MODE != 1:
                                        fibo_data['callback_rate'] = cal_callback_rate(symbol, priceEntry, pricesl)
                                elif SLShort > 0:
                                    pricesl = price_to_precision(symbol, priceEntry + (priceEntry * (SLShort / 100.0)))
                                    fibo_data['sl_txt'] = f'SL: {SLShort:.2f}% @{pricesl}'
                                    fibo_data['sl'] = pricesl
                                elif SLShort < 0:
                                    pricesl = 0.0
                                    fibo_data['sl_txt'] = f'SL: None'
                                    fibo_data['sl'] = pricesl
                                else:
                                    pricesl = fibo_data['sl']
                                    fibo_data['sl_txt'] = f'SL: (AUTO) @{pricesl}'
                                notify_msg.append(fibo_data['sl_txt'])

                                await short_TPSL(exchange, symbol, amount, priceEntry, pricetp, pricesl, closeRate)
                                print(f'[{symbol}] Set TP {pricetp} SL {pricesl}')

                            if trailingStopMode == 'on' and closeRate < 100.0:
                                notify_msg.append('# TrailingStop')
                                if priceTL == 0.0:
                                    # RR = 1
                                    activationPrice = price_to_precision(symbol, priceEntry - abs(priceEntry - pricesl))
                                else:
                                    activationPrice = priceTL
                                    
                                if callbackShort == 0.0:
                                    callbackShort = fibo_data['callback_rate']
                                    notify_msg.append(f'Call Back: (AUTO) {callbackShort:.2f}%')
                                else:
                                    notify_msg.append(f'Call Back: {callbackShort:.2f}%')

                                activatePrice = await short_TLSTOP(exchange, symbol, amount, activationPrice, callbackShort)
                                print(f'[{symbol}] Set Trailing Stop {activatePrice}')
                                # callbackShort_str = ','.join(['{:.2f}%'.format(cb) for cb in callbackShort])

                                if priceTL == 0.0:
                                    notify_msg.append(f'Active Price: (AUTO) @{activatePrice}')
                                elif config.TP_PNL_Short > 0:
                                    if config.is_percent_mode:
                                        notify_msg.append(f'Active Price PNL: {config.Active_TL_PNL_Short:.2f}% @{activatePrice}')
                                    else:
                                        notify_msg.append(f'Active Price PNL: {config.Active_TL_PNL_Short:.2f}$ @{activatePrice}')
                                elif activeTLShort > 0:
                                    notify_msg.append(f'Active Price: {activeTLShort:.2f}% @{activatePrice}')

                            gather( line_chart(symbol, df, '\n'.join(notify_msg), 'SHORT', fibo_data, **kwargs) )

                elif tradeMode != 'on' :
                    fibo_data['tp_txt'] = 'TP'
                    fibo_data['sl_txt'] = 'SL'
                    gather( line_chart(symbol, df, f'{symbol}\nสถานะ : Short\nADX : {round(adxLast,1)}\nRSI : {round(rsi[1],1)}\nSTOk : {round(stoK[1],1)}', 'SHORT', fibo_data, **kwargs) )

    except Exception as ex:
        print(type(ex).__name__, symbol, str(ex))
        logger.exception(f'go_trade {symbol}')
        line_notify_err(f'แจ้งปัญหาเหรียญ {symbol}\nการเทรดผิดพลาด: {ex}')
        pass

async def load_all_symbols():
    global all_symbols, watch_list
    try:
        exchange = await getExchange()

        # t1=time.time()
        markets = await exchange.fetch_markets()
        # print(markets[0])
        mdf = pd.DataFrame(markets, columns=['id','quote','symbol','limits','precision','info','settle'])
        # mdf.drop(mdf[~mdf.quote.isin(config.MarginType)].index, inplace=True)
        mdf.drop(mdf[~mdf.settle.isin(config.MarginType)].index, inplace=True)
        mdf.drop(mdf[mdf['id'].str.contains('_')].index, inplace=True)
        # print(mdf.head())
        # all_symbols = {r['id']:{'symbol':r['symbol'],'minAmount':r['minAmount']} for r in mdf[~mdf['id'].isin(drop_value)][['id','symbol','minAmount']].to_dict('records')}
        # all_symbols = {r['id']:{'symbol':r['symbol'],'minCost':r['minCost']} for r in mdf[~mdf['id'].isin(drop_value)][['id','symbol','minCost']].to_dict('records')}
        all_symbols = {r['id']:{
            'symbol':r['symbol'],
            'quote':r['quote'],
            'leverage':1,
            'amount_precision':int(r['precision']['amount']),
            'price_precision':int(r['precision']['price']),
            'limits_amount_min':int(r['limits']['amount']['min']),
            'limits_price_min':int(r['limits']['price']['min']),
            } for r in mdf[['id','symbol','quote','precision','info','limits']].to_dict('records')}
        # print(all_symbols, len(all_symbols))
        # print(all_symbols.keys())
        if len(config.watch_list) > 0:
            watch_list_tmp = list(filter(lambda x: x in all_symbols.keys(), config.watch_list))
        else:
            watch_list_tmp = all_symbols.keys()
        # remove sysbol if in back_list
        watch_list = list(filter(lambda x: x not in config.back_list, watch_list_tmp))
        # print(watch_list)
        # print([all_symbols[s] for s in all_symbols.keys() if s in watch_list])
        # t2=(time.time())-t1
        # print(f'ใช้เวลาหาว่ามีเหรียญ เทรดฟิวเจอร์ : {t2:0.2f} วินาที')

        print(f'total     : {len(all_symbols.keys())} symbols')
        print(f'target    : {len(watch_list)} symbols')

        logger.info(f'all:{len(all_symbols.keys())} watch:{len(watch_list)}')

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('load_all_symbols')

    finally:
        if exchange:
            await exchange.close()

async def set_all_leverage():
    try:
        exchange = await getExchange()

        if config.automaxLeverage == 'on':
            print('auto max leverage...')
            leverages = await exchange.fapiPrivateGetLeverageBracket()
            def get_max_leverage(symbol):
                leverage = [x for x in leverages if x['symbol'] == symbol][0]
                if leverage:
                    return max([int(x['initialLeverage']) for x in leverage['brackets']])
                else:
                    return config.Leverage
            # ตั้ง leverage ให้เท่ากับ max leverage ของแต่ละเหรียญ
            loops = [set_leverage(exchange, symbol, get_max_leverage(symbol)) for symbol in watch_list]
        else:
            # set default leverage
            loops = [set_leverage(exchange, symbol, config.Leverage) for symbol in watch_list]
        await gather(*loops)

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('set_all_leverage')

    finally:
        if exchange:
            await exchange.close()

async def fetch_first_ohlcv():
    try:
        exchange = await getExchange()

        # ครั้งแรกอ่าน 1000 แท่ง -> CANDLE_LIMIT
        limit = CANDLE_LIMIT

        if TIMEFRAME_SECONDS[config.timeframe] >= TIMEFRAME_SECONDS[config.START_TRADE_TF]:
            # อ่านแท่งเทียนแบบ async และ เทรดตามสัญญาน
            loops = [fetch_ohlcv_trade(exchange, symbol, config.timeframe, limit) for symbol in watch_list]
            await gather(*loops)
        else:
            # อ่านแท่งเทียนแบบ async แต่ ยังไม่เทรด
            loops = [fetch_ohlcv(exchange, symbol, config.timeframe, limit) for symbol in watch_list]
            await gather(*loops)

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('fetch_first_ohlcv')

    finally:
        if exchange:
            await exchange.close()

async def fetch_next_ohlcv(next_ticker):
    try:
        exchange = await getExchange()

        # กำหนด limit การอ่านแท่งเทียนแบบ 0=ไม่ระบุจำนวน, n=จำนวน n แท่ง
        limit = 0

        # อ่านแท่งเทียนแบบ async และ เทรดตามสัญญาน
        watch_list_rand = shuffle(watch_list.copy())
        loops = [fetch_ohlcv_trade(exchange, symbol, config.timeframe, limit, next_ticker) for symbol in watch_list]
        await gather(*loops)

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('fetch_next_ohlcv')

    finally:
        if exchange:
            await exchange.close()

async def mm_strategy():
    global is_send_notify_risk
    try:
        exchange = await getExchange()

        hasMMPositions = False
        balance = await exchange.fetch_balance()
        if balance is None:
            print('เกิดข้อผิดพลาดที่ api fetch_balance')
            return
        ex_positions = balance['info']['positions']
        if len(ex_positions) == 0:
            return
        mm_positions = [position for position in ex_positions 
            if position['symbol'] in all_symbols.keys() and
                all_symbols[position['symbol']]['quote'] in config.MarginType and 
                float(position['positionAmt']) != 0]

        mm_positions = sorted(mm_positions, key=lambda k: float(k['unrealizedProfit']))

        # sumProfit = sum([float(position['unrealizedProfit']) for position in mm_positions])
        sumLongProfit = sum([float(position['unrealizedProfit']) for position in mm_positions if float(position['positionAmt']) >= 0])
        sumShortProfit = sum([float(position['unrealizedProfit']) for position in mm_positions if float(position['positionAmt']) < 0])
        sumProfit = sumLongProfit + sumShortProfit

        sumLongMargin = sum([float(position['initialMargin']) for position in mm_positions if float(position['positionAmt']) >= 0])
        sumShortMargin = sum([float(position['initialMargin']) for position in mm_positions if float(position['positionAmt']) < 0])
        sumMargin = sumLongMargin + sumShortMargin

        # count_trade = len(mm_positions)
        # count_trade_long = sum([1 for position in mm_positions if float(position['positionAmt']) >= 0])
        # count_trade_short = sum([1 for position in mm_positions if float(position['positionAmt']) < 0])

        # Money Management (MM) Strategy
        logger.debug(f'MM Profit - Long[{sumLongProfit:.4f}] + Short[{sumShortProfit:.4f}] = All[{sumProfit:.4f}]')
        # logger.debug(f'PNL: {config.TP_PNL}, {config.SL_PNL}')

        cost_rate = 1.0
        long_margin_rate = 1.0
        short_margin_rate = 1.0
        margin_rate = 1.0
        if config.is_percent_mode:
            cost_rate = config.CostAmount / 100.0
            long_margin_rate = sumLongMargin / 100.0
            short_margin_rate = sumShortMargin / 100.0
            margin_rate = sumMargin / 100.0

        tp_profit = config.TP_Profit * margin_rate
        sl_profit = config.SL_Profit * margin_rate
        tp_profit_long = config.TP_Profit_Long * long_margin_rate
        sl_profit_long = config.SL_Profit_Long * long_margin_rate
        tp_profit_short = config.TP_Profit_Short * short_margin_rate
        sl_profit_short = config.SL_Profit_Short * short_margin_rate

        logger.debug(f'MM TP/SL - All: {tp_profit:.4f}/-{sl_profit:.4f} Long: {tp_profit_long:.4f}/-{sl_profit_long:.4f} Short: {tp_profit_short:.4f}/-{sl_profit_short:.4f}')

        # close all positions by TP/SL profit setting
        if (tp_profit > 0 and sumProfit > tp_profit) or \
            (sl_profit > 0 and sumProfit < -sl_profit):

            exit_loops = []
            # cancel_loops = []
            mm_notify = []
            # exit all positions
            for position in mm_positions:
                symbol = position['symbol']
                positionAmt = float(position['positionAmt'])
                if positionAmt > 0.0:
                    print(f"[{symbol}] สถานะ : MM Long Exit processing...")
                    exit_loops.append(long_close(exchange, symbol, positionAmt))
                    # line_notify(f'{symbol}\nสถานะ : MM Long Exit\nProfit = {sumProfit}')
                    mm_notify.append(f'{symbol} : MM Long Exit')
                    # cancel_loops.append(cancel_order(exchange, symbol, 'long'))
                elif positionAmt < 0.0:
                    print(f"[{symbol}] สถานะ : MM Short Exit processing...")
                    exit_loops.append(short_close(exchange, symbol, positionAmt))
                    # line_notify(f'{symbol}\nสถานะ : MM Short Exit\nProfit = {sumProfit}')
                    mm_notify.append(f'{symbol} : MM Short Exit')
                    # cancel_loops.append(cancel_order(exchange, symbol, 'short'))

            try:
                if len(exit_loops) > 0:
                    await gather(*exit_loops)
                    hasMMPositions = True
            except Exception as ex:
                print(type(ex).__name__, str(ex))
                logger.exception('mm_strategy exit all')

            # try:
            #     if len(cancel_loops) > 0:
            #         await gather(*cancel_loops)
            # except Exception as ex:
            #     print(type(ex).__name__, str(ex))
            #     logger.exception('mm_strategy cancel all')

            if len(mm_notify) > 0:
                txt_notify = '\n'.join(mm_notify)
                line_notify(f'\nสถานะ...\n{txt_notify}\nProfit = {sumProfit:.4f}')
        
        else:

            isTPLongExit = (tp_profit_long > 0 and sumLongProfit > tp_profit_long)
            isSLLongExit = (sl_profit_long > 0 and sumLongProfit < -sl_profit_long)
            isTPShortExit = (tp_profit_short > 0 and sumShortProfit > tp_profit_short)
            isSLShortExit = (sl_profit_short > 0 and sumShortProfit < -sl_profit_short)

            # close all LONG positions by LONG TP/SL profit setting
            if isTPLongExit or isSLLongExit:
                exit_loops = []
                # cancel_loops = []
                mm_notify = []
                # exit all positions
                for position in mm_positions:
                    symbol = position['symbol']
                    positionAmt = float(position['positionAmt'])
                    if positionAmt > 0.0:
                        print(f"[{symbol}] สถานะ : MM Long Exit processing...")
                        exit_loops.append(long_close(exchange, symbol, positionAmt))
                        # line_notify(f'{symbol}\nสถานะ : MM Long Exit\nProfit = {sumProfit}')
                        mm_notify.append(f'{symbol} : MM Long Exit')
                        # cancel_loops.append(cancel_order(exchange, symbol, 'long'))

                try:
                    if len(exit_loops) > 0:
                        await gather(*exit_loops)
                        hasMMPositions = True
                except Exception as ex:
                    print(type(ex).__name__, str(ex))
                    logger.exception('mm_strategy exit long')

                # try:
                #     if len(cancel_loops) > 0:
                #         await gather(*cancel_loops)
                # except Exception as ex:
                #     print(type(ex).__name__, str(ex))
                #     logger.exception('mm_strategy cancel long')

                if len(mm_notify) > 0:
                    txt_notify = '\n'.join(mm_notify)
                    line_notify(f'\nสถานะ...\n{txt_notify}\nProfit = {sumLongProfit:.4f}')

            # close all SHORT positions by SHORT TP/SL profit setting
            if isTPShortExit or isSLShortExit:
                exit_loops = []
                # cancel_loops = []
                mm_notify = []
                # exit all positions
                for position in mm_positions:
                    symbol = position['symbol']
                    positionAmt = float(position['positionAmt'])
                    if positionAmt < 0.0:
                        print(f"[{symbol}] สถานะ : MM Short Exit processing...")
                        exit_loops.append(short_close(exchange, symbol, positionAmt))
                        # line_notify(f'{symbol}\nสถานะ : MM Short Exit\nProfit = {sumProfit}')
                        mm_notify.append(f'{symbol} : MM Short Exit')
                        # cancel_loops.append(cancel_order(exchange, symbol, 'short'))

                try:
                    if len(exit_loops) > 0:
                        await gather(*exit_loops)
                        hasMMPositions = True
                except Exception as ex:
                    print(type(ex).__name__, str(ex))
                    logger.exception('mm_strategy exit short')

                # try:
                #     if len(cancel_loops) > 0:
                #         await gather(*cancel_loops)
                # except Exception as ex:
                #     print(type(ex).__name__, str(ex))
                #     logger.exception('mm_strategy cancel short')

                if len(mm_notify) > 0:
                    txt_notify = '\n'.join(mm_notify)
                    line_notify(f'\nสถานะ...\n{txt_notify}\nProfit = {sumShortProfit:.4f}')

            # close target position by LONG/SHORT TP/SL PNL setting
            exit_loops = []
            # cancel_loops = []
            logger.debug(f'MM TP/SL PNL - Long: {config.TP_PNL_Long*cost_rate:.4f}/{-config.SL_PNL_Long*cost_rate:.4f} Short: {config.TP_PNL_Short*cost_rate:.4f}/{-config.SL_PNL_Long*cost_rate:.4f}')
            if config.TP_PNL_Long > 0 and not isTPLongExit:
                tp_lists = [position for position in mm_positions if 
                    float(position['positionAmt']) > 0.0 and 
                    float(position['unrealizedProfit']) > config.TP_PNL_Long*cost_rate]
                if len(tp_lists) > 0:
                    logger.debug(f'TP_PNL_Long {tp_lists}')
                for position in tp_lists:
                    symbol = position['symbol']
                    positionAmt = float(position['positionAmt'])
                    unrealizedProfit = float(position['unrealizedProfit'])
                    print(f"[{symbol}] สถานะ : MM Long Exit processing...")
                    exit_loops.append(long_close(exchange, symbol, positionAmt))
                    line_notify(f'{symbol}\nสถานะ : MM Long Exit\nPNL = {unrealizedProfit}')
                    # cancel_loops.append(cancel_order(exchange, symbol, 'long'))
            if config.TP_PNL_Short > 0 and not isTPShortExit:
                tp_lists = [position for position in mm_positions if 
                    float(position['positionAmt']) < 0.0 and 
                    float(position['unrealizedProfit']) > config.TP_PNL_Short*cost_rate]
                if len(tp_lists) > 0:
                    logger.debug(f'TP_PNL_Short {tp_lists}')
                for position in tp_lists:
                    symbol = position['symbol']
                    positionAmt = float(position['positionAmt'])
                    unrealizedProfit = float(position['unrealizedProfit'])
                    print(f"[{symbol}] สถานะ : MM Short Exit processing...")
                    exit_loops.append(short_close(exchange, symbol, positionAmt))
                    line_notify(f'{symbol}\nสถานะ : MM Short Exit\nPNL = {unrealizedProfit}')
                    # cancel_loops.append(cancel_order(exchange, symbol, 'short'))
            if config.SL_PNL_Long > 0 and not isSLLongExit:
                sl_lists = [position for position in mm_positions if 
                    float(position['positionAmt']) > 0.0 and 
                    float(position['unrealizedProfit']) < -config.SL_PNL_Long*cost_rate]
                if len(sl_lists) > 0:
                    logger.debug(f'SL_PNL_Long {sl_lists}')
                for position in sl_lists:
                    symbol = position['symbol']
                    positionAmt = float(position['positionAmt'])
                    unrealizedProfit = float(position['unrealizedProfit'])
                    print(f"[{symbol}] สถานะ : MM Long Exit processing...")
                    exit_loops.append(long_close(exchange, symbol, positionAmt))
                    line_notify(f'{symbol}\nสถานะ : MM Long Exit\nPNL = {unrealizedProfit}')
                    # cancel_loops.append(cancel_order(exchange, symbol, 'long'))
            if config.SL_PNL_Short > 0 and not isSLShortExit:
                sl_lists = [position for position in mm_positions if 
                    float(position['positionAmt']) < 0.0 and 
                    float(position['unrealizedProfit']) < -config.SL_PNL_Long*cost_rate]
                if len(sl_lists) > 0:
                    logger.debug(f'SL_PNL_Short {sl_lists}')
                for position in sl_lists:
                    symbol = position['symbol']
                    positionAmt = float(position['positionAmt'])
                    unrealizedProfit = float(position['unrealizedProfit'])
                    print(f"[{symbol}] สถานะ : MM Short Exit processing...")
                    exit_loops.append(short_close(exchange, symbol, positionAmt))
                    line_notify(f'{symbol}\nสถานะ : MM Short Exit\nPNL = {unrealizedProfit}')
                    # cancel_loops.append(cancel_order(exchange, symbol, 'short'))

            try:
                if len(exit_loops) > 0:
                    await gather(*exit_loops)
                    hasMMPositions = True
            except Exception as ex:
                print(type(ex).__name__, str(ex))
                logger.exception('mm_strategy exit pnl')
            # try:
            #     if len(cancel_loops) > 0:
            #         await gather(*cancel_loops)
            # except Exception as ex:
            #     print(type(ex).__name__, str(ex))
            #     logger.exception('mm_strategy cancel pnl')

        if hasMMPositions == False:
            # notify risk
            # balance = await exchange.fetch_balance()
            # if balance is None:
            #     print('เกิดข้อผิดพลาดที่ api fetch_balance')
            #     return
            # ex_positions = balance['info']['positions']

            for marginType in config.MarginType:
                marginAsset = [asset for asset in balance['info']['assets'] if asset['asset'] == marginType][0]
                availableBalance = float(marginAsset['availableBalance'])
                initialMargin = float(marginAsset['initialMargin'])
                maintMargin = float(marginAsset['maintMargin'])
                # maintMarginCal = config.maint_margin_ratio * initialMargin
                if initialMargin > 0:
                    config.maint_margin_ratio = maintMargin / initialMargin
                totalRisk = 0.0
                if (availableBalance + initialMargin) > 0:
                    totalRisk = (maintMargin) / (availableBalance + initialMargin) * 100
                logger.debug(f'maintMargin {maintMargin} ({config.maint_margin_ratio}) risk {totalRisk}')
                if is_send_notify_risk == False and (config.risk_limit > 0) and (totalRisk > config.risk_limit):
                    is_send_notify_risk = True
                    logger.debug(f'MM {marginType} Risk Alert: {totalRisk:,.2f}% (limit {config.risk_limit:,.2f}%)')
                    line_notify(f'แจ้งเตือน\n{marginType} Risk Alert: {totalRisk:,.2f}% (limit {config.risk_limit:,.2f}%)')
                elif totalRisk < config.risk_limit - 10.0:
                    is_send_notify_risk = False

            # clear margin
            exit_loops = []
            # cancel_loops = []
            mm_notify = []
            # exit all positions
            for position in mm_positions:
                symbol = position['symbol']
                initialMargin = float(position['initialMargin'])
                if initialMargin <= config.Clear_Magin:
                    print('remove', symbol, initialMargin)
                    positionAmt = float(position['positionAmt'])
                    if positionAmt > 0.0:
                        print(f"[{symbol}] สถานะ : MM Long Exit processing...")
                        exit_loops.append(long_close(exchange, symbol, positionAmt))
                        # line_notify(f'{symbol}\nสถานะ : MM Long Exit\nProfit = {sumProfit}')
                        mm_notify.append(f'{symbol} : MM Long Remove')
                        # cancel_loops.append(cancel_order(exchange, symbol, 'long'))
                    elif positionAmt < 0.0:
                        print(f"[{symbol}] สถานะ : MM Short Exit processing...")
                        exit_loops.append(short_close(exchange, symbol, positionAmt))
                        # line_notify(f'{symbol}\nสถานะ : MM Short Exit\nProfit = {sumProfit}')
                        mm_notify.append(f'{symbol} : MM Short Remove')
                        # cancel_loops.append(cancel_order(exchange, symbol, 'short'))

            try:
                if len(exit_loops) > 0:
                    await gather(*exit_loops)
            except Exception as ex:
                print(type(ex).__name__, str(ex))
                logger.exception('mm_strategy clear exit')

            # try:
            #     if len(cancel_loops) > 0:
            #         await gather(*cancel_loops)
            # except Exception as ex:
            #     print(type(ex).__name__, str(ex))
            #     logger.exception('mm_strategy clear cancel')

            if len(mm_notify) > 0:
                txt_notify = '\n'.join(mm_notify)
                line_notify(f'\nสถานะ: Margin <= {config.Clear_Magin}\n{txt_notify}')

        #loss counter
        if config.Loss_Limit > 0:
            for symbol in orders_history.keys():
                if orders_history[symbol]['last_loss'] >= config.Loss_Limit and symbol in watch_list:
                    watch_list.remove(symbol)
                    print(f'{symbol} removed from watch_list, last loss = {orders_history[symbol]["last_loss"]}')
                    logger.info(f'{symbol} removed from watch_list, last loss = {orders_history[symbol]["last_loss"]}')

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('mm_strategy')
        line_notify_err(f'แจ้งปัญหาระบบ mm\nข้อผิดพลาด: {str(ex)}')

    finally:
        if exchange:
            await exchange.close()

async def update_all_positions():
    global all_positions, orders_history
    try:
        exchange = await getExchange()

        balance = await exchange.fetch_balance()
        if balance is None:
            print('เกิดข้อผิดพลาดที่ api fetch_balance')
            return None
        # print(balance)
        ex_positions = balance['info']['positions']
        positions = [position for position in ex_positions 
            if position['symbol'] in all_symbols.keys() and
                all_symbols[position['symbol']]['quote'] in config.MarginType and 
                float(position['positionAmt']) != 0]

        positions = sorted(positions, key=lambda k: float(k['unrealizedProfit']), reverse=True)

        all_positions = pd.DataFrame(positions, columns=POSITION_COLUMNS)
        all_positions["positionSide"] = all_positions['positionAmt'].apply(lambda x: 'LONG' if float(x) >= 0 else 'SHORT')
        all_positions["quote"] = all_positions['symbol'].apply(lambda x: all_symbols[x]['quote'])
        all_positions['unrealizedProfit'] = all_positions['unrealizedProfit'].apply(lambda x: '{:.4f}'.format(float(x)))
        all_positions['initialMargin'] = all_positions['initialMargin'].apply(lambda x: '{:.4f}'.format(float(x)))

        # update open order
        loops = [update_open_orders(exchange, symbol) for symbol in all_positions['symbol'].unique()]
        await gather(*loops)

        def f(x):
            if x is None:
                return '......'
            try:
                symbol = x['symbol']
                if is_positionside_dual:
                    positionSide = str(x['positionSide']).lower()
                else:
                    positionSide = 'both'
                if symbol in orders_history.keys() \
                    and positionSide in orders_history[symbol]['orders_open'].keys():
                    return ''.join(orders_history[symbol]['orders_open'][positionSide])
                else:
                    return '......'
            except:
                return '......'
        # logger.debug(all_positions.apply(f, axis=1))
        all_positions['orders'] = all_positions.apply(f, axis=1)

        # clear order if no positions
        loops = []
        for symbol in orders_history.keys():
            for positionSide in orders_history[symbol]['positions'].keys():
                if 'status' in orders_history[symbol]['positions'][positionSide].keys() \
                    and orders_history[symbol]['positions'][positionSide]['status'] == 'open' \
                    and symbol not in all_positions['symbol'].to_list():
                    orders_history[symbol]['positions'][positionSide]['status'] = 'close'
                    loops.append(cancel_order(exchange, symbol, positionSide))
        await gather(*loops)

        keysList = list(orders_history.keys())
        logger.debug(f'symbol orders history: {keysList}')
        save_orders_history_csv(history_file_csv)
        save_orders_history_json(history_json_path)

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('update_all_positions')
        line_notify_err(f'แจ้งปัญหาระบบ update positions\nข้อผิดพลาด: {str(ex)}')
        balance = None

    finally:
        if exchange:
            await exchange.close()

    return balance

async def update_all_balance(notifyLine=False):
    global balance_entry, balalce_total, count_trade, count_trade_long, count_trade_short, total_risk, total_margin
    try:
        balance = await update_all_positions()
        if balance is None:
            print('เกิดข้อผิดพลาดที่ ระบบ update balance')
            return
        count_trade = len(all_positions)
        count_trade_long = sum(all_positions["positionSide"].map(lambda x : x == 'LONG'))
        count_trade_short = sum(all_positions["positionSide"].map(lambda x : x == 'SHORT'))
        
        ub_msg = []
        ub_msg.append('รายงานสรุป')
        ub_msg.append(f'{bot_name} {bot_vesion}')

        if config.limit_Trade > 0:
            ub_msg.append(f"# Count Trade\nLong+Short: {count_trade}/{config.limit_Trade}")
            print(f"Count Trade : {count_trade}/{config.limit_Trade}")
        else:
            ub_msg.append(f"# Count Trade\nLong: {count_trade_long}/{config.limit_Trade_Long}\nShort: {count_trade_short}/{config.limit_Trade_Short}")
            print(f"Count Trade : Long: {count_trade_long}/{config.limit_Trade_Long} Short: {count_trade_short}/{config.limit_Trade_Short}")

        balance_entry = { marginType:0.0 for marginType in config.MarginType}
        balalce_total = 0.0

        for marginType in config.MarginType:
            report_msg = []
            margin_positions = all_positions[all_positions['quote'] == marginType]
            margin_positions.reset_index(drop=True, inplace=True)
            margin_positions.index = margin_positions.index + 1
            # sumProfit = margin_positions['unrealizedProfit'].astype('float64').sum()
            # sumMargin = margin_positions['initialMargin'].astype('float64').sum()
            # total = (balance_entry[marginType] + sumMargin + sumProfit)

            marginAsset = [asset for asset in balance['info']['assets'] if asset['asset'] == marginType][0]
            balance_entry[marginType] = float(marginAsset['availableBalance'])
            sumProfit = float(marginAsset['unrealizedProfit'])
            sumMargin = float(marginAsset['initialMargin'])
            marginBalance = float(marginAsset['marginBalance'])
            # walletBalance = float(marginAsset['walletBalance'])
            # balance_cal = (balance_entry[marginType] + sumMargin + sumProfit)
            balalce_total += marginBalance

            maintMargin = float(marginAsset['maintMargin'])
            if sumMargin > 0:
                config.maint_margin_ratio = maintMargin / sumMargin

            totalRisk = 0.0
            if (balance_entry[marginType] + sumMargin) > 0:
                totalRisk = (maintMargin) / (balance_entry[marginType] + sumMargin) * 100
            total_risk[marginType] = totalRisk
            total_margin[marginType] = sumMargin

            margin_positions.columns = POSITION_COLUMNS_RENAME
            if len(margin_positions) > 0:
                print(margin_positions[POSITION_COLUMNS_DISPLAY])
            else:
                print('No Positions')
            # ub_msg.append(f"# {marginBalance:,.4f} {marginType}\nFree: {balance_entry[marginType]:,.4f}\nMargin: {sumMargin:,.4f}\nProfit: {sumProfit:+,.4f}")
            report_msg.append(f"Balance : {marginBalance:,.4f} {marginType}\nFree : {balance_entry[marginType]:,.4f} Margin : {sumMargin:,.4f}\n\nProfit : {sumProfit:+,.4f}")
            print(f"Balance === {marginBalance:,.4f} {marginType} Free: {balance_entry[marginType]:,.4f} Margin: {sumMargin:,.4f} Profit: {sumProfit:+,.4f}")
            risk_txt = ' (no limit)'
            if config.risk_limit > 0:
                risk_txt = f' (limit {config.risk_limit:,.2f}%)'
            # ub_msg.append(f"Risk: {totalRisk:,.2f}%{risk_txt}")
            report_msg.append(f"\nRisk : {totalRisk:,.2f}%{risk_txt}")
            print(f"Risk ====== {totalRisk:,.2f}%{risk_txt}")
            if totalRisk > config.risk_limit:
                is_send_notify_risk = True
            if len(margin_positions) > 0 and notifyLine and config.LastNotifyTime < time.time():
                local_time = time.ctime(time.time())
                report_msg.append(f'\nBot Last Processing : == {local_time} ==')
                await line_report(marginType, margin_positions[POSITION_COLUMNS_DISPLAY], '\n'.join(report_msg), sumProfit >= 0)
            
        balance_change = balalce_total - start_balance_total if start_balance_total > 0 else 0
        ub_msg.append(f"# Total {balalce_total:,.4f}\n# Change {balance_change:+,.4f}")
        print(f"Total ===== {balalce_total:,.4f} Change: {balance_change:+,.4f}")

        if notifyLine and config.LastNotifyTime < time.time():
            config.LastNotifyTime += TIMEFRAME_SECONDS['1h']
            line_notify('\n'.join(ub_msg))
            
        logger.info(f'countTrade:{count_trade} (L:{count_trade_long},S:{count_trade_short}) balance_entry:{balance_entry} sumMargin:{sumMargin} sumProfit:{sumProfit} totalRisk:{totalRisk}')

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('update_all_balance')
        line_notify_err(f'แจ้งปัญหาระบบ update balance\nข้อผิดพลาด: {str(ex)}')

async def load_symbols_setting():
    global symbols_setting
    try:
        if config.CSV_NAME:
            symbols_setting = pd.read_csv(config.CSV_NAME, skipinitialspace=True)
            if any(x in CSV_COLUMNS for x in symbols_setting.columns.to_list()):
                symbols_setting.drop(symbols_setting[~symbols_setting.margin_type.isin(config.MarginType)].index, inplace=True)
                symbols_setting['id'] = symbols_setting['symbol']+symbols_setting['margin_type']
                symbols_setting.set_index('id', inplace=True)
                # เอาอันซ้ำออก เหลืออันใหม่สุด
                symbols_setting = symbols_setting[~symbols_setting.index.duplicated(keep='last')]

                # validate all values
                int_columns = [
                        'fast_value', 'mid_value', 'slow_value', 'signal_index', 'leverage'
                        ]
                float_columns = [
                        'cost_amount', 
                        'tp_long', 'tp_close_long', 'sl_long', 'callback_long', 'active_tl_long',
                        'tp_short', 'tp_close_short', 'sl_short', 'callback_short', 'active_tl_short'
                        ]
                symbols_setting[int_columns] = symbols_setting[int_columns].apply(pd.to_numeric, errors='coerce')
                symbols_setting[float_columns] = symbols_setting[float_columns].apply(pd.to_numeric, downcast='float', errors='coerce')
                symbols_setting.dropna(inplace=True)

                # print(symbols_setting.head())
                # print(symbols_setting.iloc[1])
                # validate all setting

                logger.info(f'success load symbols_setting from {config.CSV_NAME}')
            else:
                symbols_setting = pd.DataFrame(columns=CSV_COLUMNS)
                print(f'fail load symbols_setting from {config.CSV_NAME}, all columns not match')
                logger.info(f'fail load symbols_setting from {config.CSV_NAME}, all columns not match')

    except Exception as ex:
        symbols_setting = pd.DataFrame(columns=CSV_COLUMNS)
        print(type(ex).__name__, str(ex))
        logger.exception('load_symbols_setting')

async def close_non_position_order(watch_list, positions_list):
    try:
        exchange = await getExchange()

        loops = [cancel_order(exchange, symbol, 'all') for symbol in watch_list if symbol not in positions_list]
        await gather(*loops)
    
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('update_all_balance')

    finally:
        if exchange:
            await exchange.close()

async def get_currentmode():
    positionside_dual = False
    try:
        exchange = await getExchange()
        result = await exchange.fapiPrivateGetPositionSideDual()
        positionside_dual = result['dualSidePosition']
        print('positionside_dual:', positionside_dual)
        logger.info(f'positionside_dual: {positionside_dual}')
        
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('get_currentmode')

    finally:
        if exchange:
            await exchange.close()

    return positionside_dual

async def main():
    global start_balance_total, is_send_notify_risk, is_positionside_dual

    marginList = ','.join(config.MarginType)
    if config.SANDBOX:
        bot_title = f'{bot_fullname} - {config.timeframe} - {marginList} (SANDBOX)'
    else:
        bot_title = f'{bot_fullname} - {config.timeframe} - {marginList}'

    # set cursor At top, left (1,1)
    print(CLS_SCREEN+bot_title)

    await load_all_symbols()

    await load_symbols_setting()

    await set_all_leverage()

    is_positionside_dual = await get_currentmode()

    load_orders_history_json(history_json_path)

    t1 = time.time()
    config.LastNotifyTime = t1 - (t1 % TIMEFRAME_SECONDS['1h'])

    # แสดงค่า positions & balance
    await update_all_balance(notifyLine=config.SummaryReport)
    start_balance_total = balalce_total

    if config.IS_CLEAR_OLD_ORDER:
        await close_non_position_order(watch_list, all_positions['symbol'].to_list())
    else:
        print(f'skip close_non_position_order')

    time_wait = TIMEFRAME_SECONDS[config.timeframe] # กำหนดเวลาต่อ 1 รอบ
    time_wait_ub = UB_TIMER_SECONDS[config.UB_TIMER_MODE] # กำหนดเวลา update balance
    if config.MM_TIMER_MIN == 0.0:
        time_wait_mm = time_wait_ub
    else:
        time_wait_mm = config.MM_TIMER_MIN*60

    # อ่านแท่งเทียนทุกเหรียญ
    t1=time.time()
    local_time = time.ctime(t1)
    print(f'get all candles: {local_time}')

    await fetch_first_ohlcv()
        
    t2=(time.time())-t1
    print(f'total time : {t2:0.2f} secs')
    logger.info(f'first ohlcv: {t2:0.2f} secs')

    try:
        start_ticker = time.time()
        next_ticker = start_ticker - (start_ticker % time_wait) # ตั้งรอบเวลา
        next_ticker += time_wait # กำหนดรอบเวลาถัดไป
        next_ticker_ub = start_ticker - (start_ticker % time_wait_ub)
        next_ticker_ub += time_wait_ub
        next_ticker_mm = start_ticker - (start_ticker % time_wait_mm)
        next_ticker_mm += time_wait_mm
        while True:
            seconds = time.time()

            if seconds >= next_ticker + TIME_SHIFT: # ครบรอบ
                # set cursor At top, left (1,1)
                print(CLS_SCREEN+bot_title)

                local_time = time.ctime(seconds)
                print(f'calculate new indicator: {local_time}')

                await update_all_balance(notifyLine=config.SummaryReport)

                t1=time.time()

                await fetch_next_ohlcv(next_ticker)

                t2=(time.time())-t1
                print(f'total time : {t2:0.2f} secs')
                logger.info(f'update ohlcv: {t2:0.2f} secs (include trade)')

                next_ticker += time_wait # กำหนดรอบเวลาถัดไป
                next_ticker_ub += time_wait_ub
                next_ticker_mm += time_wait_mm

                is_send_notify_risk = False
                line_notify_last_err()

                await sleep(10)

            else:
                # mm strategy
                if config.Trade_Mode == 'on' and seconds >= next_ticker_mm:
                    await mm_strategy()
                    next_ticker_mm += time_wait_mm
                    line_notify_last_err()
                # display position
                if config.Trade_Mode == 'on' and seconds >= next_ticker_ub + TIME_SHIFT:
                    # set cursor At top, left (1,1)
                    print(CLS_SCREEN+bot_title)
                    balance_time = time.ctime(seconds)
                    print(f'last indicator: {local_time}, last balance: {balance_time}')
                    await update_all_balance()
                    next_ticker_ub += time_wait_ub
                    line_notify_last_err()

            await sleep(1)

    except KeyboardInterrupt:
        pass

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('main')


async def waiting():
    count = 0
    status = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    while True:
        await sleep(1)
        print('\r'+CRED+CBOLD+status[count%len(status)]+' waiting...\r'+CEND, end='')
        count += 1
        count = count%len(status)

if __name__ == "__main__":
    try:
        pathlib.Path('./plots').mkdir(parents=True, exist_ok=True)
        pathlib.Path('./logs').mkdir(parents=True, exist_ok=True)
        pathlib.Path('./datas').mkdir(parents=True, exist_ok=True)

        history_file_csv = './datas/orders_history.csv'
        history_json_path = './datas/orders_history.json'

        logger = logging.getLogger("App Log")
        logger.setLevel(config.LOG_LEVEL)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler = RotatingFileHandler('./logs/app.log', maxBytes=250000, backupCount=10)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info('start ==========')
        os.system("color") # enables ansi escape characters in terminal
        print(HIDE_CURSOR, end="")
        loop = get_event_loop()
        # แสดง status waiting ระหว่างที่รอ...
        loop.create_task(waiting())
        loop.run_until_complete(main())   

    except KeyboardInterrupt:
        print(CLS_LINE+'\rbye')

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('app')
        line_notify(f'{bot_name} bot stop')

    finally:
        print(SHOW_CURSOR, end="")
        # save data
        # if os.path.exists(history_file_csv):
        #     os.rename(history_file_csv, history_file_csv.replace('.csv', f'{DATE_SUFFIX}.csv'))
        # save_orders_history_json(history_json_path)
