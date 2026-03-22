import pandas as pd
import numpy as np
from typing import Optional

def calculate_zscore(spread: pd.Series, window: int = 20) -> pd.Series:
    """
    spread の rolling z-score を計算する
    """
    mean = spread.rolling(window=window).mean()
    std = spread.rolling(window=window).std()

    std = std.replace(0, np.nan)
    zscore = (spread - mean) / std
    return zscore

def generate_positions(
    zscore: pd.Series,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5,
    stop_threshold: Optional[float] = None
) -> pd.Series:
    """
    zscore からペアトレードの保有ポジションを作る

    Parameters
    ----------
    zscore : pd.Series
        spread の rolling z-score
    entry_threshold : float
        エントリー閾値
    exit_threshold : float
        通常のイグジット閾値
    stop_threshold : float | None
        ストップロス閾値
        None の場合はストップロスなし

    Returns
    -------
    positions : pd.Series
        1  = ロングスプレッド保有
        -1 = ショートスプレッド保有
        0  = ノーポジション
    """
    positions = pd.Series(index=zscore.index, dtype="float64")
    position = 0

    for i in range(len(zscore)):
        z = zscore.iloc[i]

        if pd.isna(z):
            positions.iloc[i] = 0
            continue

        # ノーポジション時のエントリー
        if position == 0:
            if z <= -entry_threshold:
                position = 1   # ロングスプレッド
            elif z >= entry_threshold:
                position = -1  # ショートスプレッド

        # ロングスプレッド保有時
        elif position == 1:
            # stop loss
            if stop_threshold is not None and z <= -stop_threshold:
                position = 0
            # normal exit
            elif z >= -exit_threshold:
                position = 0

        # ショートスプレッド保有時
        elif position == -1:
            # stop loss
            if stop_threshold is not None and z >= stop_threshold:
                position = 0
            # normal exit
            elif z <= exit_threshold:
                position = 0

        positions.iloc[i] = position

    return positions