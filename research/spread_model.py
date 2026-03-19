import numpy as np
import pandas as pd
import statsmodels.api as sm


def fit_ols_spread(y: pd.Series, x: pd.Series) -> dict:
    """
    OLS回帰で spread(residuals) を作る

    Parameters
    ----------
    y : pd.Series
    x : pd.Series

    Returns
    -------
    dict
        {
            "alpha": float,
            "beta": float,
            "spread": pd.Series,
            "residuals": pd.Series
        }
    """
    pair = pd.concat([y, x], axis=1).dropna()
    y_clean = pair.iloc[:, 0]
    x_clean = pair.iloc[:, 1]

    x_const = sm.add_constant(x_clean)
    model = sm.OLS(y_clean, x_const).fit()

    alpha = model.params.iloc[0]
    beta = model.params.iloc[1]
    residuals = model.resid

    return {
        "alpha": alpha,
        "beta": beta,
        "residuals": residuals
    }


def calculate_half_life(spread: pd.Series) -> float:
    """
    spread の half-life を計算する
    """
    spread = spread.dropna()

    lag_spread = spread.shift(1)
    delta_spread = spread - lag_spread

    df = pd.concat([lag_spread, delta_spread], axis=1).dropna()
    df.columns = ["lag_spread", "delta_spread"]

    beta = np.polyfit(df["lag_spread"], df["delta_spread"], 1)[0]

    if len(df) < 20:
        return np.nan

    if beta >= 0:
        return np.nan

    half_life = -np.log(2) / beta

    if half_life <= 0 or not np.isfinite(half_life):
        return np.nan
    
    if half_life > 252:
        return np.nan

    return half_life


def calculate_zscore(spread: pd.Series, window: int = 20) -> pd.Series:
    """
    spread の rolling z-score を計算する
    """
    mean = spread.rolling(window=window).mean()
    std = spread.rolling(window=window).std()

    std = std.replace(0, np.nan)
    zscore = (spread - mean) / std
    return zscore

def build_pair_model(price_df: pd.DataFrame, s1: str, s2: str) -> dict:
    log_pair = np.log(price_df[[s1, s2]].dropna())
    fitted = fit_ols_spread(log_pair[s1], log_pair[s2])
    half_life = calculate_half_life(fitted["spread"])

    return {
        "pair": (s1, s2),
        "alpha": fitted["alpha"],
        "beta": fitted["beta"],
        "spread": fitted["spread"],
        "half_life": half_life
    }