import os
import yfinance as yf
import pandas as pd
from config.settings import START_DATE, MAX_TICKERS

# CACHE_FILE = "data/cache/price_cache.csv"

def load_price_data(tickers, start=START_DATE, end=None):

    cache_path = f"data/cache/price_{start}_{end}.csv"
    
    # テスト用制限
    tickers = tickers[:MAX_TICKERS]

    print("=================")
    print(tickers)

    # キャッシュ確認
    if os.path.exists(cache_path):
        price = pd.read_csv(cache_path, index_col=0, parse_dates=True)

        if not price.empty:
            print("キャッシュ使用")
            return price
        else:
            print("キャッシュが壊れているので再取得")

    print("ダウンロード開始")

    try:
        data = yf.download(
            tickers,
            start=start,
            auto_adjust=True,
            progress=False,
            threads=False
        )
    except Exception as e:
        raise RuntimeError(f"データ取得失敗: {e}")

    print("ダウンロード終了")

    if data.empty:
        raise ValueError("取得データが空です")

    if "Close" not in data:
        raise ValueError("Closeデータが存在しません")

    price = data["Close"]

    if price.empty:
        raise ValueError("価格データが空です")

    # データクリーニング
    price = price.dropna(axis=1, thresh=len(price)*0.95)
    price = price.ffill()

    if price.empty:
        raise ValueError("クリーニング後データが空です")

    # キャッシュ保存
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    price.to_csv(cache_path)

    return price

def load_pair_data(ticker_y, ticker_x, start="2022-01-01"):

    data = yf.download(
        [ticker_y, ticker_x],
        start=start
    )["Close"]

    data = data.dropna()

    price_y = data[ticker_y]
    price_x = data[ticker_x]

    return price_y, price_x

def load_test_pair():
    # トヨタ（7203.T） - ホンダ（7267.T）
    # みずほ（8411.T） - 三菱UFJ（8306.T）
    # 東京エレクトロン（8035.T） - アドバンテスト（6857.T）
    # toyota = "7203.T"
    # honda = "7267.T"
    mizuho = "8411.T"
    mitsubishi = "8306.T"
    # toere = "8035.T"
    # advantest = "6857.T"
    return load_pair_data(mizuho, mitsubishi)