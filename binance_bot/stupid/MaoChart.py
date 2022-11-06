from signal import signal
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
# import pandas_ta as ta
import numpy as np
from datetime import datetime
import os

def Make_Graph(df, filename, ticket_symbol, tf_label, tf_count=100, signal_idx = -1, trend='long'):
    iday = df.tail(tf_count)
    iday['time'] = iday['time'].map(pd.to_datetime)
    iday.set_index('time', inplace=True)
    iday_minmax = iday[:tf_count+signal_idx+1]
    minimum_index = iday_minmax['low'].idxmin()
    minimum_price = iday_minmax['low'].min()
    maximum_index = iday_minmax['high'].idxmax()
    maximum_price = iday_minmax['high'].max()
    # print('min:',minimum_index,minimum_price)
    # print('max:',maximum_index,maximum_price)

    #Calculate the max high and min low price
    difference = maximum_price - minimum_price #Get the difference
    
    #Calculate fibo
    # a1 = minimum_price + difference * 0.1618
    # first_level = minimum_price + difference * 0.236
    # second_level = minimum_price + difference * 0.382
    # third_level = minimum_price + difference * 0.5
    # fourth_level = minimum_price + difference * 0.618
    # fifth_level = minimum_price + difference * 0.786

    fibo_colors = ['red','brown','orange','yellow','green','blue','gray','purple','purple','purple']
    fibo_rvalues = [0,0.1618,0.236,0.382,0.5,0.618,0.786,1]
    fibo_xvalues = [0,0.1618,0.236,0.382,0.5,0.618,0.786,1,1.382,1.618]
    minmax_points = []

    if trend.lower() == 'long':
        isFiboRetrace = datetime.strptime(str(minimum_index), '%Y-%m-%d %H:%M:%S') > datetime.strptime(str(maximum_index), '%Y-%m-%d %H:%M:%S')
        # print(isFiboRetrace)

        if isFiboRetrace:
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((minimum_index,minimum_price))
            fibo_values = fibo_rvalues
            fibo_levels = []
            for fibo_val in fibo_values:
                fibo_level = minimum_price + difference * fibo_val
                fibo_levels.append(fibo_level)
        else:
            maxidx = np.where(iday_minmax.index==maximum_index)[0][0]
            # print(maxidx)
            new_minimum_index = iday_minmax['low'].iloc[maxidx:].idxmin()
            new_minimum_price = iday_minmax['low'].iloc[maxidx:].min()
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((new_minimum_index,new_minimum_price))
            fibo_values = fibo_xvalues
            fibo_levels = []
            for fibo_val in fibo_values:
                fibo_level = new_minimum_price + difference * fibo_val
                fibo_levels.append(fibo_level)
    else:
        isFiboRetrace = datetime.strptime(str(minimum_index), '%Y-%m-%d %H:%M:%S') < datetime.strptime(str(maximum_index), '%Y-%m-%d %H:%M:%S')
        # print(isFiboRetrace)

        fibo_colors = ['red','brown','orange','yellow','green','blue','gray','purple','purple','purple']
        if isFiboRetrace:
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((maximum_index,maximum_price))
            fibo_values = fibo_rvalues
            fibo_levels = []
            for fibo_val in fibo_values:
                fibo_level = maximum_price - difference * fibo_val
                fibo_levels.append(fibo_level)
        else:
            minidx = np.where(iday_minmax.index==minimum_index)[0][0]
            # print(maxidx)
            new_maximum_index = iday_minmax['high'].iloc[minidx:].idxmax()
            new_maximum_price = iday_minmax['high'].iloc[minidx:].max()
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((new_maximum_index,new_maximum_price))
            fibo_values = fibo_xvalues
            fibo_levels = []
            for fibo_val in fibo_values:
                fibo_level = new_maximum_price - difference * fibo_val
                fibo_levels.append(fibo_level)

    colors = ['green' if value >= 0 else 'red' for value in iday['MACD']]
    apds = [mpf.make_addplot(iday['EWMbase'],color='red'),
            mpf.make_addplot(iday['EWMfast'],color='magenta'),
            mpf.make_addplot(iday['EWMslow'],color='orange'),
            mpf.make_addplot(iday['MACD'],type='bar',width=0.7,panel=2,color=colors),
            mpf.make_addplot(iday['MACDs'],panel=2,color='b'),
        ]
    fibo_lines = dict(
        hlines=fibo_levels,
        colors=fibo_colors,
        alpha=0.5,
        linestyle='-.',
        linewidths=1,
        )
    minmax_lines = dict(
        alines=minmax_points,
        colors='blue',
        # linestyle='-.',
        linewidths=0.5,
        )
    # print(iday.columns)
    # print(iday.index[signal_idx])
    signal_line = dict(
        x=tf_count+signal_idx,
        color='red',
        # alpha=0.5,
        linestyle=':',
        linewidth=0.5,
        )
    kws = dict(
        volume=True,volume_panel=1,
        hlines=fibo_lines,
        alines=minmax_lines,
        figscale=1.5,
        figratio=(8, 6),
        panel_ratios=(8,3,3),
        addplot=apds,
        scale_padding={'left': 0.5, 'top': 0.8, 'right': 1.1, 'bottom': 0.5},
        )

    myrcparams = {'axes.labelsize':10,'xtick.labelsize':8,'ytick.labelsize':8}
    mystyle = mpf.make_mpf_style(base_mpf_style='yahoo',rc=myrcparams)

    filename = f'plots\{ticket_symbol}.png'
    fig, axlist = mpf.plot(iday,**kws,type='ohlc',style=mystyle,returnfig=True)
    
    for ax in axlist:
        ax.axvline(**signal_line)

    axlist[0].xaxis.set_label_position('top')
    axlist[0].set_title(f'{trend.upper()} {ticket_symbol} at {iday.index[signal_idx]}')
    if isFiboRetrace:
        axlist[0].set_xlabel(f'(fibo retractment, tf({tf_label})={tf_count})')
    else:
        axlist[0].set_xlabel(f'(fibo extension, tf({tf_label})={tf_count})')

    for idx, fibo_val in enumerate(fibo_values):
        axlist[0].text(0,fibo_levels[idx],f'{fibo_val}({fibo_levels[idx]:.4f})',fontsize=8,color=fibo_colors[idx],horizontalalignment='right')

    # mpf.show()
    fig.savefig(filename)

    # clear memory
    # for ax in axlist:
    #     del ax
    # del fig

    plt.close('all')