import numpy as np
from config.settings import CORR_THRESHOLD

def find_high_corr_pairs(price_df, threshold=CORR_THRESHOLD):

    log_price = np.log(price_df)
    returns = log_price.diff().dropna()

    corr_matrix = returns.corr()
    corr_values = corr_matrix.values

    mask = corr_values > threshold
    mask = np.triu(mask, k=1)

    rows, cols = np.where(mask)

    col_names = corr_matrix.columns

    pairs = [
        (col_names[r], col_names[c], corr_values[r, c])
        for r, c in zip(rows, cols)
    ]

    pairs.sort(key=lambda x: x[2], reverse=True)

    return pairs

def find_corr_pairs_within_industries(price_df, industry_groups, corr_threshold=CORR_THRESHOLD):
    """
    業界ごとに相関ペアを抽出する
    """
    all_corr_pairs = []

    for industry, group_tickers in industry_groups.items():
        if len(group_tickers) < 2:
            continue

        sub_price = price_df[group_tickers]
        pairs = find_high_corr_pairs(sub_price, threshold=corr_threshold)

        print(f"{industry}: {len(pairs)}ペア")
        all_corr_pairs.extend(pairs)

    return all_corr_pairs