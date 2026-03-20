from data.data_loader import load_price_data
from universe.universe import load_universe_tickers
tickers = load_universe_tickers()

prices = load_price_data(tickers)

print(prices.head())
print(prices.shape)