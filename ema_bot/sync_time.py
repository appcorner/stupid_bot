import datetime
import time
import os

try:
    import ntplib
    client = ntplib.NTPClient()
    print(datetime.datetime.now())
    print("before sync")
    response = client.request('pool.ntp.org')
    print(response.offset)
    print(time.ctime(response.tx_time))
    print("time sync")
    os.system('net start w32time')
    os.system('w32tm /resync')
    os.system('net stop w32time')
    print("after sync")
    response = client.request('pool.ntp.org')
    print(response.offset)
    print(time.ctime(response.tx_time))
except Exception as ex:
    print(ex)
    print('Could not sync with time server.')

input("Press Enter to continue...")
print('Done.')