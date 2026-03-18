import os
import pandas as pd

CSV_PATH = "data/raw/jpx_list.csv"
XLS_PATH = "data/raw/jpx_list.xls"

def load_universe():

    # CSVがなければExcelから作る
    if not os.path.exists(CSV_PATH):
        print("CSVがないのでExcelから作成します")

        if not os.path.exists(XLS_PATH):
            raise FileNotFoundError("Excelファイルが存在しません")

        df = pd.read_excel(XLS_PATH)
        df.columns = df.columns.str.strip()

        if df.empty:
            raise ValueError("Excelデータが空です")

        df.to_csv(CSV_PATH, index=False)

    # CSV読み込み
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()

    if df.empty:
        raise ValueError("CSVデータが空です")

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