import logging
import sys
import time

from pyexchange.erisx import ErisxApi


logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(threadName)-18s %(message)s', level=logging.DEBUG)
client = ErisxApi(fix_trading_endpoint=sys.argv[1], fix_trading_user=sys.argv[2],
                  fix_marketdata_endpoint=sys.argv[3], fix_marketdata_user=sys.argv[4],
                  password=sys.argv[5],
                  clearing_url="https://clearing.newrelease.erisx.com/api/v1/",
                  api_key=sys.argv[6], api_secret=sys.argv[7])
# print(sys.argv)
print("ErisxApi created\n")

# print(client.get_balances())
time.sleep(15)

print(f"Received security list with message length {len(str(client.get_markets()))}")
time.sleep(25)

print("Disconnecting")
del client
time.sleep(2)
