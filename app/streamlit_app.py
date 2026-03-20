import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd

from config.settings import START_DATE, CORR_THRESHOLD, PVALUE_THRESHOLD
from universe.universe import load_universe_tickers, build_industry_map, load_universe_df
from data.data_loader import load_price_data
from research.pair_finder import find_high_corr_pairs
from research.industry_filter import filter_pairs_by_industry
from research.cointegration import filter_cointegrated_pairs
from research.spread_model import build_pair_model

st.set_page_config(page_title="PairLab", layout="wide")

st.title("📈 PairLab")
st.caption("日本株ペアトレード候補抽出ツール")

with st.sidebar:
    st.header("設定")
    start_date = st.text_input("開始日", START_DATE)
    corr_th = st.slider("相関しきい値", 0.5, 0.99, CORR_THRESHOLD)
    pval_th = st.slider("cointegration p値", 0.001, 0.1, PVALUE_THRESHOLD)
    max_half_life = st.slider("half-life 上限", 1, 252, 60)
    run = st.button("実行")

if not run:
    st.stop()

with st.spinner("銘柄取得中..."):
    tickers = load_universe_tickers()
st.success(f"{len(tickers)}銘柄")

with st.spinner("価格取得中..."):
    price_df = load_price_data(tickers, start=start_date)
st.success("価格取得完了")

with st.spinner("相関フィルター..."):
    corr_pairs = find_high_corr_pairs(price_df, threshold=corr_th)
st.write(f"相関ペア数: {len(corr_pairs)}")

with st.spinner("業界フィルター..."):
    universe_df = load_universe_df()
    industry_map = build_industry_map(universe_df, industry_col="33業種区分")
    industry_pairs = filter_pairs_by_industry(corr_pairs, industry_map)
st.write(f"業界フィルター通過ペア数: {len(industry_pairs)}")

with st.spinner("cointegration検定..."):
    coint_results = filter_cointegrated_pairs(price_df, industry_pairs)

if len(coint_results) == 0:
    st.warning("cointegrationを通過したペアがありません。")
    st.stop()

rows = []
for item in coint_results:
    s1, s2 = item["pair"]
    pair_model = build_pair_model(price_df, s1, s2)

    rows.append({
        "pair": item["pair"],
        "corr": item["corr"],
        "pvalue": item["pvalue"],
        "beta": pair_model["beta"],
        "half_life": pair_model["half_life"],
    })

result_df = pd.DataFrame(rows)
result_df = result_df[result_df["pvalue"] < pval_th]
result_df = result_df[result_df["half_life"].notna()]
result_df = result_df[result_df["half_life"] <= max_half_life]
result_df = result_df.sort_values(["pvalue", "half_life"], ascending=[True, True])

st.subheader("最終ペア")
st.dataframe(result_df)

if len(result_df) > 0:
    selected = st.selectbox("ペア選択", result_df["pair"].tolist())
    s1, s2 = selected

    st.subheader(f"{s1} vs {s2}")

    pair_price = price_df[[s1, s2]].dropna()
    norm = pair_price / pair_price.iloc[0]
    st.line_chart(norm)

    pair_model = build_pair_model(price_df, s1, s2)
    st.line_chart(pair_model["spread"])

    st.write({
        "pair": pair_model["pair"],
        "alpha": pair_model["alpha"],
        "beta": pair_model["beta"],
        "half_life": pair_model["half_life"],
    })