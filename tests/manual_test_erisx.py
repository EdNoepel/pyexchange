import sys

from pyexchange.erisx import ErisxApi


client = ErisxApi(fix_trading_endpoint=sys.argv[1], fix_trading_user=sys.argv[2],
                  fix_marketdata_endpoint=sys.argv[3], fix_marketdata_user=sys.argv[4],
                  password=sys.argv[5],
                  clearing_url="https://clearing.newrelease.erisx.com/api/v1/",
                  api_key=sys.argv[6], api_secret=sys.argv[7])

print(sys.argv)
print("ErisxApi created\n")


def test_get_balances():
    print(client.get_balances())


test_get_balances()
