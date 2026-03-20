import numpy as np
import pandas as pd

def generate_positions(
    zscore: pd.Series,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5
) -> pd.Series:
    """
    z-score から日次ポジションを作る

    1  : long spread
    -1 : short spread
    0  : no position
    """
    position = pd.Series(index=zscore.index, dtype=float)
    current_pos = 0

    for dt in zscore.index:
        z = zscore.loc[dt]

        if pd.isna(z):
            position.loc[dt] = current_pos
            continue

        if current_pos == 0:
            if z < -entry_threshold:
                current_pos = 1
            elif z > entry_threshold:
                current_pos = -1
        else:
            if abs(z) < exit_threshold:
                current_pos = 0

        position.loc[dt] = current_pos

    return position


def calculate_pair_returns(
    price_y: pd.Series,
    price_x: pd.Series,
    beta: float,
    position: pd.Series
) -> pd.DataFrame:
    """
    ペアのポジションから日次損益率を計算する
    """
    df = pd.concat(
        [price_y.rename("y"), price_x.rename("x"), position.rename("position")],
        axis=1
    ).dropna()

    df["ret_y"] = df["y"].pct_change()
    df["ret_x"] = df["x"].pct_change()

    # 未来データ混入を防ぐため1日ずらす
    df["position_lag"] = df["position"].shift(1).fillna(0)

    spread_ret = df["ret_y"] - beta * df["ret_x"]
    df["strategy_ret"] = df["position_lag"] * spread_ret
    df["strategy_ret"] = df["strategy_ret"].fillna(0)

    df["equity_curve"] = (1 + df["strategy_ret"]).cumprod()

    return df


def calculate_performance(strategy_ret: pd.Series) -> dict:
    """
    基本成績を計算
    """
    strategy_ret = strategy_ret.dropna()

    if len(strategy_ret) == 0:
        return {
            "total_return": np.nan,
            "annual_return": np.nan,
            "annual_vol": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
            "win_rate": np.nan,
        }

    equity = (1 + strategy_ret).cumprod()

    total_return = equity.iloc[-1] - 1
    annual_return = equity.iloc[-1] ** (252 / len(strategy_ret)) - 1
    annual_vol = strategy_ret.std() * np.sqrt(252)
    sharpe = np.nan if annual_vol == 0 or np.isnan(annual_vol) else annual_return / annual_vol

    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = drawdown.min()

    win_rate = (strategy_ret > 0).mean()

    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "annual_vol": annual_vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
    }