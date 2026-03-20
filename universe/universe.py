import os
import pandas as pd

CSV_PATH = "data/raw/jpx_list.csv"
XLS_PATH = "data/raw/jpx_list.xls"

def load_universe_tickers():

    # CSVがなければExcelから作る
    if not os.path.exists(CSV_PATH):
        print("CSVがないのでExcelから作成します")

        if not os.path.exists(XLS_PATH):
            raise FileNotFoundError("Excelファイルが存在しません")

        df = pd.read_excel(XLS_PATH)
        df.columns = df.columns.str.strip()

        if df.empty:
            raise ValueError("Excelデータが空です")

        # ETF・ETN除外
        df = df[~df["市場・商品区分"].astype(str).str.contains("ETF|ETN", na=False)]
        df.to_csv(CSV_PATH, index=False)

    # CSV読み込み
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()

    if df.empty:
        raise ValueError("CSVデータが空です")
    
    # ETF・ETN除外
    df = df[~df["市場・商品区分"].astype(str).str.contains("ETF|ETN", na=False)]

    # カラムチェック
    if "コード" not in df.columns:
        raise ValueError("コード列が見つかりません")

    # 銘柄コード処理
    codes = df["コード"].dropna().astype(str)
    codes = codes[codes.str.len() == 4]

    if len(codes) == 0:
        raise ValueError("有効な銘柄コードがありません")

    tickers = (codes + ".T").tolist()

    print(f"{len(tickers)}銘柄読み込み")

    return tickers

def load_universe_df() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()

    if df.empty:
        raise ValueError("CSVデータが空です")

    return df


def build_industry_map(df: pd.DataFrame, industry_col: str = "33業種区分") -> dict:
    """
    銘柄コード -> 業界名 の辞書を作る

    Parameters
    ----------
    df : pd.DataFrame
        JPX銘柄一覧
    industry_col : str
        "33業種区分" または "17業種区分"

    Returns
    -------
    dict
        例:
        {
            "7203.T": "輸送用機器",
            "6758.T": "電気機器",
        }
    """
    work = df.copy()

    # コードを yfinance 形式に合わせる
    work["ticker"] = work["コード"].astype(str).str.strip() + ".T"

    # 業界情報が欠けている行は除外
    work = work.dropna(subset=[industry_col])

    industry_map = dict(zip(work["ticker"], work[industry_col]))
    return industry_map