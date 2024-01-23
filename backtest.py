import pandas as pd
import numpy as np
import ccxt  # pip install ccxt
import json
import time


conf_file = ("conf.json")
with open(conf_file, 'r') as myfile:
    data = myfile.read()
    configs = json.loads(data)


# Load historical price data for Bitcoin from Binance
btc_usdt = ccxt.binance({
    'apiKey': configs["API_KEY"],
    'secret': configs["SECRET_KEY"]
}).fetch_ohlcv('BTC/USDT', '1h')
df = pd.DataFrame(btc_usdt, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

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

# Implement a trading loop to execute trades
position = 0
cash = 10000
for i in range(len(df)):
    if df['signal'].iloc[i] != 0:
        position += df['signal'].iloc[i] * cash / df['close'].iloc[i]
        cash = 0
    cash += df['close'].iloc[i] * df['volume'].iloc[i] / 100000000
print(f'Ending balance: {cash + position * df["close"].iloc[-1]}')