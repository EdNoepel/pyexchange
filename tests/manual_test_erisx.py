import sys

from pyexchange.erisx import ErisxApi


client = ErisxApi(fix_endpoint="127.0.0.1:1752", sender_comp_id="unknown", username="unknown", password="unknown",
                  clearing_url="https://clearing.newrelease.erisx.com/api/v1/",
                  api_secret=sys.argv[1], api_key=sys.argv[2])

print(sys.argv)
print("ErisxApi created\n")


def test_get_balances():
    print(client.get_balances())


test_get_balances()
