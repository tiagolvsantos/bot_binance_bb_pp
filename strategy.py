import pandas as pd
import numpy as np
import tabulate as tb
import ccxt  # pip install ccxt
import json
import time


conf_file = ("conf.json")
with open(conf_file, 'r') as myfile:
    data = myfile.read()
    configs = json.loads(data)


# Load historical price data for Bitcoin from Binance
def get_quote(symbol, resolution):
    data_quote = ccxt.binance({
        'apiKey': configs["API_KEY"],
        'secret': configs["SECRET_KEY"]
    }).fetch_ohlcv(symbol, resolution)
    df = pd.DataFrame(data_quote, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df


def compute_signal(df):
    # Compute Bollinger Bands
    df['sma'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper_band'] = df['sma'] + 3 * df['std']
    df['lower_band'] = df['sma'] - 3 * df['std']

    # Compute pivot points
    df['pp'] = (df['high'] + df['low'] + df['close']) / 3
    df['r1'] = (2 * df['pp']) - df['low']
    df['s1'] = (2 * df['pp']) - df['high']
    df['r2'] = df['pp'] + (df['high'] - df['low'])
    df['s2'] = df['pp'] - (df['high'] - df['low'])

    # Define trading signals
    df['long_signal'] = np.where((df['close'] < df['lower_band']) & (df['close'] < df['s1']), 1, 0)
    df['short_signal'] = np.where((df['close'] > df['upper_band']) & (df['close'] > df['r1']), -1, 0)
    df['signal'] = df['long_signal'] + df['short_signal']
    print(tb.tabulate(df.tail(1), headers='keys', tablefmt='fancy_outline', showindex="never"))
    return df


# Implement a trading loop to execute trades
def execute_trade(df, exchange, position, cash, symbol):
    # Compute the current position size
    position_size = position * df['close'].iloc[-1]

    # Check for trading signals
    if df['signal'].iloc[-1] != 0:
        print( f"Signal {df['signal'].iloc[-1]}")
        # Calculate the amount to be traded based on the current position and cash balance
        if df['signal'].iloc[-1] == 1:
            # Long trade
            trade_amount = (cash + position_size) / df['close'].iloc[-1]
        else:
            # Short trade
            trade_amount = position_size / df['close'].iloc[-1]

        # Place a limit order on the Binance exchange
        if trade_amount > 0:
            print( f"Create buy limit order")
            order = exchange.create_limit_buy_order(symbol, trade_amount, df['close'].iloc[-1])
        else:
            print( f"Create sell limit order")
            order = exchange.create_limit_sell_order(symbol, -trade_amount, df['close'].iloc[-1])

        # Update the position and cash balance
        position += df['signal'].iloc[-1] * trade_amount
        cash = (1 - df['signal'].iloc[-1]) * trade_amount
        print(f"Position {position}   | Cash: {cash}")


while True:
    try:
        #####################################################
        resolution = "15m"
        symbol="BTC/USDT"
        position = 0
        cash = 1000
        #####################################################
        exchange = ccxt.binance({
            'apiKey': configs["API_KEY"],
            'secret': configs["SECRET_KEY"]
            })
        df = get_quote(symbol, resolution)
        execute_trade(compute_signal(df), exchange, position, cash, symbol)
        time.sleep(60)
    except Exception as e:
        print(e)
        time.sleep(60)