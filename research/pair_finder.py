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