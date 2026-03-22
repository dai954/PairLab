import pandas as pd

from strategy.pairs_signal import calculate_zscore, generate_positions
from backtest.backtest_engine import run_backtest, calculate_performance, create_trade_log


def run_parameter_search(
    price_df: pd.DataFrame,
    s1: str,
    s2: str,
    beta: float,
    spread: pd.Series,
    entry_list: list[float],
    exit_list: list[float],
    window: int = 20,
    stop_threshold: float = 3.5,
) -> pd.DataFrame:
    """
    1ペアに対して entry / exit のパラメータ比較を行う

    Parameters
    ----------
    price_df : pd.DataFrame
        全銘柄の価格データ
    s1, s2 : str
        ペア銘柄
    beta : float
        hedge ratio
    spread : pd.Series
        spread 系列
    entry_list : list[float]
        entry threshold 候補
    exit_list : list[float]
        exit threshold 候補
    window : int
        zscore rolling window
    stop_threshold : float
        stop threshold

    Returns
    -------
    pd.DataFrame
        パラメータ比較結果
    """
    results = []

    for entry_threshold in entry_list:
        for exit_threshold in exit_list:
            zscore = calculate_zscore(spread, window=window)

            positions = generate_positions(
                zscore=zscore,
                entry_threshold=entry_threshold,
                exit_threshold=exit_threshold,
                stop_threshold=stop_threshold,
            )

            bt = run_backtest(
                price_y=price_df[s1],
                price_x=price_df[s2],
                beta=beta,
                positions=positions,
            )

            metrics = calculate_performance(bt["strategy_return"])
            trade_log = create_trade_log(bt, zscore)

            trade_count = len(trade_log)
            avg_holding_days = (
                trade_log["holding_days"].mean() if trade_count > 0 else 0
            )
            trade_win_rate = (
                (trade_log["pnl"] > 0).mean() if trade_count > 0 else 0
            )

            results.append({
                "entry": entry_threshold,
                "exit": exit_threshold,
                "window": window,
                "stop": stop_threshold,
                "total_return": metrics["total_return"],
                "annual_return": metrics["annual_return"],
                "annual_vol": metrics["annual_vol"],
                "sharpe": metrics["sharpe"],
                "max_drawdown": metrics["max_drawdown"],
                "daily_win_rate": metrics["win_rate"],
                "trade_count": trade_count,
                "trade_win_rate": trade_win_rate,
                "avg_holding_days": avg_holding_days,
            })

    return pd.DataFrame(results)