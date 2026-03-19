import os
import yfinance as yf
import pandas as pd
from config.settings import START_DATE, MAX_TICKERS

CACHE_FILE = "data/cache/price_cache.csv"

def load_price_data(tickers, start=START_DATE):

    # テスト用制限
    tickers = tickers[:MAX_TICKERS]

    print("=================")
    print(tickers)

    # キャッシュ確認
    if os.path.exists(CACHE_FILE):
        price = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)

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
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    price.to_csv(CACHE_FILE)

    return price