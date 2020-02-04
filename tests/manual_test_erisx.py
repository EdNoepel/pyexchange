import logging
import sys
import time

from pyexchange.erisx import ErisxApi


logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.DEBUG)
client = ErisxApi(fix_trading_endpoint=sys.argv[1], fix_trading_user=sys.argv[2],
                  fix_marketdata_endpoint=sys.argv[3], fix_marketdata_user=sys.argv[4],
                  password=sys.argv[5],
                  clearing_url="https://clearing.newrelease.erisx.com/api/v1/",
                  api_key=sys.argv[6], api_secret=sys.argv[7])
print(sys.argv)
print("ErisxApi created\n")


def test_get_balances():
    print(client.get_balances())


time.sleep(5)
test_get_balances()
del client
time.sleep(3)
