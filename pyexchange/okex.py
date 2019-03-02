# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import urllib
import hashlib
from pprint import pformat
from typing import List

import requests

from pyexchange.model import Candle
from pymaker.numeric import Wad
from pymaker.util import http_response_summary


class Order:
    def __init__(self, order_id: int, timestamp: int, pair: str,
                 is_sell: bool, price: Wad, amount: Wad, deal_amount: Wad):
        assert(isinstance(order_id, int))
        assert(isinstance(timestamp, int))
        assert(isinstance(pair, str))
        assert(isinstance(is_sell, bool))
        assert(isinstance(price, Wad))
        assert(isinstance(amount, Wad))
        assert(isinstance(deal_amount, Wad))

        self.order_id = order_id
        self.timestamp = timestamp
        self.pair = pair
        self.is_sell = is_sell
        self.price = price
        self.amount = amount
        self.deal_amount = deal_amount

    @property
    def sell_to_buy_price(self) -> Wad:
        return self.price

    @property
    def buy_to_sell_price(self) -> Wad:
        return self.price

    @property
    def remaining_buy_amount(self) -> Wad:
        return (self.amount - self.deal_amount)*self.price if self.is_sell else (self.amount - self.deal_amount)

    @property
    def remaining_sell_amount(self) -> Wad:
        return (self.amount - self.deal_amount) if self.is_sell else (self.amount - self.deal_amount)*self.price

    def __eq__(self, other):
        assert(isinstance(other, Order))

        return self.order_id == other.order_id and \
               self.pair == other.pair

    def __hash__(self):
        return hash((self.order_id, self.pair))

    def __repr__(self):
        return pformat(vars(self))


class Trade:
    def __init__(self,
                 trade_id: id,
                 timestamp: int,
                 is_sell: bool,
                 price: Wad,
                 amount: Wad,
                 amount_symbol: str):
        assert(isinstance(trade_id, int))
        assert(isinstance(timestamp, int))
        assert(isinstance(is_sell, bool))
        assert(isinstance(price, Wad))
        assert(isinstance(amount, Wad))
        assert(isinstance(amount_symbol, str))

        self.trade_id = trade_id
        self.timestamp = timestamp
        self.is_sell = is_sell
        self.price = price
        self.amount = amount
        self.amount_symbol = amount_symbol

    def __eq__(self, other):
        assert(isinstance(other, Trade))
        return self.trade_id == other.trade_id and \
               self.timestamp == other.timestamp and \
               self.is_sell == other.is_sell and \
               self.price == other.price and \
               self.amount == other.amount and \
               self.amount_symbol == other.amount_symbol

    def __hash__(self):
        return hash((self.trade_id,
                     self.timestamp,
                     self.is_sell,
                     self.price,
                     self.amount,
                     self.amount_symbol))

    def __repr__(self):
        return pformat(vars(self))


class OKEXApi:
    """OKCoin and OKEX API interface.

    Developed according to the following manual:
    <https://www.okex.com/intro_apiOverview.html>.

    Inspired by the following example:
    <https://github.com/OKCoin/rest>, <https://github.com/OKCoin/rest/tree/master/python>.
    """

    logger = logging.getLogger()

    def __init__(self, api_server: str, api_key: str, secret_key: str, timeout: float):
        assert(isinstance(api_server, str))
        assert(isinstance(api_key, str))
        assert(isinstance(secret_key, str))
        assert(isinstance(timeout, float))

        self.api_server = api_server
        self.api_key = api_key
        self.secret_key = secret_key
        self.timeout = timeout

    # Is this supposed to get account details for a particular pair?
    def ticker(self, pair: str):
        assert(isinstance(pair, str))
        return self._http_get("/api/v1/ticker.do", f"symbol={pair}")

    # Retrieves entire depth of order book.
    def depth(self, pair: str):
        assert(isinstance(pair, str))
        return self._http_get(f"/api/spot/v3/instruments/{pair}/book", {})

    # Retrieves market data.
    # What is "size" supposed to do?
    def candles(self, pair: str, type: str, size: int) -> List[Candle]:
        assert(isinstance(pair, str))
        assert(isinstance(type, str))
        assert(isinstance(size, int))

        # TODO: This is for backwards compatability.  Look into whether this
        # should simply be exposed as integer for seconds.
        assert(type in ("1min", "3min", "5min", "15min", "30min", "1day", "3day", "1week",
                        "1hour", "2hour", "4hour","6hour", "12hour"))
        granularity_in_seconds = {
            "1min": 60,
            "3min": 180,
            "5min": 300,
            "15min": 900,
            "30min": 1800,
            "1day": 3600*24,
            "3day": 3600*24*3,
            "1week": 3600*24*7,
            "1hour": 3600,
            "2hour": 3600*2,
            "4hour": 3600*4,
            "6hour": 3600*6,
            "12hour": 3600*12
        }
        assert(type in granularity_in_seconds)

        result = self._http_get(f"/api/spot/v3/instruments/{pair}/candles",
                                f"instrument_id={pair}&granularity={granularity_in_seconds[granularity]}")
        # v1 implementation passed f"symbol={pair}&type={type}&size={size}", False)

        return list(map(lambda item: Candle(timestamp=int(item[0]/1000),
                                            open=Wad.from_number(item[1]),
                                            close=Wad.from_number(item[4]),
                                            high=Wad.from_number(item[2]),
                                            low=Wad.from_number(item[3]),
                                            volume=Wad.from_number(item[5])), result))

    # New API provides balance for each token.  How to map to the V1 object?
    def get_balances(self) -> dict:
        return self._http_post("/api/account/v3/wallet", {})["info"]["funds"]

    # TODO: Figure out what this method used to do.
    # Retrieves first 100 current open orders for a pair.
    # Pass pair="" to retrieve open orders for all pairs.
    def get_orders(self, pair: str) -> List[Order]:
        assert(isinstance(pair, str))

        result = self._http_post("/api/spot/v3/orders_pending", {
            'instrument_id': pair,
            'order_id': '-1'
        })

        orders = filter(self._filter_order, result['orders'])
        return list(map(self._parse_order, orders))

    # TODO: Figure out what this method used to do.
    # Retrieves order details for a particular pair.
    def get_orders_history(self, pair: str, number_of_orders: int) -> List[Order]:
        assert(isinstance(pair, str))
        assert(isinstance(number_of_orders, int))

        orders = []
        page_length = 200
        for page in range(1, 100):
            result = self._http_post("/api/spot/v3/orders.do", {
                'instrument_id': pair,
                'status': 100,
                'current_page': page,
                'page_length': page_length
            })['orders']

            orders = orders + list(filter(self._filter_order, result))

            if len(result) == 0:
                break

            if len(result) < page_length:
                break

            if len(orders) >= number_of_orders:
                break

        return list(map(self._parse_order, orders[:number_of_orders]))

    # Submits and awaits acknowledgement of a limit order, returning the order id.
    def place_order(self, pair: str, is_sell: bool, price: Wad, amount: Wad) -> int:
        assert(isinstance(pair, str))
        assert(isinstance(is_sell, bool))
        assert(isinstance(price, Wad))
        assert(isinstance(amount, Wad))

        self.logger.info(f"Placing order ({'SELL' if is_sell else 'BUY'}, amount {amount} of {pair},"
                         f" price {price})...")

        result = self._http_post("/api/spot/v3/orders", {
            'instrument_id': pair,
            'type': 'limit',
            'side': 'sell' if is_sell else 'buy',
            'price': float(price),
            'size': float(amount)
        })
        order_id = int(result['order_id'])

        self.logger.info(f"Placed order ({'SELL' if is_sell else 'BUY'}, amount {amount} of {pair},"
                         f" price {price}) as #{order_id}")

        return order_id

    # Synchronously cancels an order.
    def cancel_order(self, order_id: int) -> bool:
        assert(isinstance(order_id, int))

        self.logger.info(f"Cancelling order #{order_id}...")

        result = self._http_post("/api/spot/v3/cancel_orders", {
            'order_id': order_id
        })
        success = int(result['order_id']) == order_id

        if success:
            self.logger.info(f"Cancelled order #{order_id}")
        else:
            self.logger.info(f"Failed to cancel order #{order_id}")

        return success

    # TODO: Seems this is now supported through /api/spot/v3/instruments/<instrument_id>/trades;
    # add support for pagination and wire it up.
    def get_trades(self, pair: str, page_number: int = 1):
        assert(isinstance(pair, str))
        assert(isinstance(page_number, int))
        raise Exception("get_trades() not available for OKEX")

    # TODO: Map this to /api/spot/v3/instruments/<instrument_id>/trades
    def get_all_trades(self, pair: str, page_number: int = 1) -> List[Trade]:
        assert(isinstance(pair, str))
        assert(isinstance(page_number, int))
        assert(page_number == 1)

        result = self._http_get("/api/v1/trades.do", f"symbol={pair}", False)
        return list(map(lambda item: Trade(trade_id=item['tid'],
                                           timestamp=item['date'],
                                           is_sell=item['type'] == 'sell',
                                           price=Wad.from_number(item['price']),
                                           amount=Wad.from_number(item['amount']),
                                           amount_symbol=pair.split('_')[0].lower()), result))

    @staticmethod
    def _filter_order(item: dict) -> bool:
        assert(isinstance(item, dict))
        return item['side'] in ['buy', 'sell']

    # TODO: Update this to match the v3 JSON
    @staticmethod
    def _parse_order(item: dict) -> Order:
        assert(isinstance(item, dict))
        return Order(order_id=item['order_id'],
                     timestamp=int(item['create_date']/1000),
                     pair=item['symbol'],
                     is_sell=item['type'] == 'sell',
                     price=Wad.from_number(item['price']),
                     amount=Wad.from_number(item['amount']),
                     deal_amount=Wad.from_number(item['deal_amount']))

    def _create_signature(self, params: dict):
        assert(isinstance(params, dict))

        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) + '&'
        data = sign + 'secret_key=' + self.secret_key
        return hashlib.md5(data.encode("utf8")).hexdigest().upper()

    # TODO: Adjust the error messages
    @staticmethod
    def _result(result, check_result: bool) -> dict:
        assert(isinstance(check_result, bool))

        if not result.ok:
            raise Exception(f"OKCoin API invalid HTTP response: {http_response_summary(result)}")

        try:
            data = result.json()
        except Exception:
            raise Exception(f"OKCoin API invalid JSON response: {http_response_summary(result)}")

        if check_result:
            if 'error_code' in data:
                raise Exception(f"OKCoin API negative response: {http_response_summary(result)}")

            if 'result' not in data or data['result'] is not True:
                raise Exception(f"OKCoin API negative response: {http_response_summary(result)}")

        return data

    def _http_get(self, resource: str, params: str, check_result: bool = True):
        assert(isinstance(resource, str))
        assert(isinstance(params, str))
        assert(isinstance(check_result, bool))

        return self._result(requests.get(url=f"{self.api_server}{resource}?{params}",
                                         timeout=self.timeout), check_result)

    def _http_post(self, resource: str, params: dict):
        assert(isinstance(resource, str))
        assert(isinstance(params, dict))

        params['api_key'] = self.api_key
        params['sign'] = self._create_signature(params)

        return self._result(requests.post(url=f"{self.api_server}{resource}",
                                          data=urllib.parse.urlencode(params),
                                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                                          timeout=self.timeout), True)
