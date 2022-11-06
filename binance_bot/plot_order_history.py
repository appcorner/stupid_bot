from application.core.PerformanceReader import PerformanceChartDrawer

order_history_file_name = 'order_history/05Dec2021_1948.json'
order_name_list = ['Momentum_LONG_0',
                   'Momentum_LONG_1',
                   'Momentum_SHORT_0',
                   'Momentum_SHORT_1',
                   'Total']

PerformanceChartDrawer(order_name_list, order_history_file_name).display_chart()
