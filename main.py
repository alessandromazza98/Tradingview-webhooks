from flask import Flask, request, render_template
import json
import config
from binance.client import Client
from binance.enums import *
import math

app = Flask(__name__, template_folder='templates')

client = Client(config.API_KEY, config.API_SECRET, testnet=True)
info = client.futures_exchange_info()


def round_decimals_down(number: float, decimals: int = 2):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor


def get_precision(symbol):
    for x in info['symbols']:
        if x['symbol'] == symbol:
            return x['quantityPrecision']
    return "Simbolo non esistente!"


def order(side, quantity, symbol, reduce_only, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"sending order {order_type} - {side} {quantity} {symbol}")
        order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity,
                                            reduceOnly=reduce_only)
        print(order)
    except Exception as e:
        print("an exception occurred - {}".format(e))
        return False
    return order


@app.route("/bella-bro")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/webhook", methods=['POST'])
def webhook():
    data = json.loads(request.data)

    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Invalid passphrase"
        }

    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']
    ticker = data['ticker']
    reduce_only = data['reduce_only']
    # round quantity to max precision
    quantity = float(round_decimals_down(quantity, get_precision(ticker)))
    order_response = order(side, quantity, ticker, reduce_only)

    if order_response:
        return {
            "code": "success",
            "message": data
        }
    else:
        print("order failed")
        return {
            "code": "error",
            "message": "order failed"
        }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    api_key = request.values.get('api_key')
    api_secret = request.values.get('api_secret')
    if api_key == config.API_KEY and api_secret == config.API_SECRET:
        response = '{"passphrase": "abc123", "exchange": "BINANCE", "ticker": "BTCUSDT", "reduce_only": "true", "strategy": {"order_action": "{{strategy.order.action}}", "order_contracts": {{strategy.order.contracts}}}}'
        return json.dumps(response)
    else:
        return "Utente non registrato!"