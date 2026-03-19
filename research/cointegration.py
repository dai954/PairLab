import numpy as np
from statsmodels.tsa.stattools import coint


def filter_cointegrated_pairs(price_df, pairs, pvalue_threshold=0.05, min_samples=200):
    """
    相関フィルターを通過したペアに対して cointegration 検定を行う

    Parameters
    ----------
    price_df : pd.DataFrame
        終値データ
    pairs : list of tuple
        [(s1, s2, corr), ...]
    pvalue_threshold : float
        p値の採用基準
    min_samples : int
        最低必要サンプル数

    Returns
    -------
    list of dict
        [
            {
                "pair": (s1, s2),
                "corr": corr,
                "pvalue": pvalue
            },
            ...
        ]
    """
    log_price = np.log(price_df)
    results = []

    for s1, s2, corr in pairs:
        pair = log_price[[s1, s2]].dropna()

        if len(pair) < min_samples:
            continue

        _, pvalue, _ = coint(pair[s1], pair[s2])

        if pvalue < pvalue_threshold:
            results.append({
                "pair": (s1, s2),
                "corr": corr,
                "pvalue": pvalue
            })

    return results