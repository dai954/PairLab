# import numpy as np
# import pandas as pd

# def run_backtest(
#     price_y: pd.Series,
#     price_x: pd.Series,
#     beta: float,
#     position: pd.Series
# ) -> pd.DataFrame:
#     """
#     ペアのポジションから日次損益率を計算する
#     """
#     df = pd.concat(
#         [price_y.rename("y"), price_x.rename("x"), position.rename("position")],
#         axis=1
#     ).dropna()

#     df["ret_y"] = df["y"].pct_change()
#     df["ret_x"] = df["x"].pct_change()

#     # 未来データ混入を防ぐため1日ずらす
#     df["position_lag"] = df["position"].shift(1).fillna(0)

#     spread_ret = df["ret_y"] - beta * df["ret_x"]
#     df["strategy_ret"] = df["position_lag"] * spread_ret
#     df["strategy_ret"] = df["strategy_ret"].fillna(0)

#     df["equity_curve"] = (1 + df["strategy_ret"]).cumprod()

#     return df


# def calculate_performance(strategy_ret: pd.Series) -> dict:
#     """
#     基本成績を計算
#     """
#     strategy_ret = strategy_ret.dropna()

#     if len(strategy_ret) == 0:
#         return {
#             "total_return": np.nan,
#             "annual_return": np.nan,
#             "annual_vol": np.nan,
#             "sharpe": np.nan,
#             "max_drawdown": np.nan,
#             "win_rate": np.nan,
#         }

#     equity = (1 + strategy_ret).cumprod()

#     total_return = equity.iloc[-1] - 1
#     annual_return = equity.iloc[-1] ** (252 / len(strategy_ret)) - 1
#     annual_vol = strategy_ret.std() * np.sqrt(252)
#     sharpe = np.nan if annual_vol == 0 or np.isnan(annual_vol) else annual_return / annual_vol

#     running_max = equity.cummax()
#     drawdown = equity / running_max - 1
#     max_drawdown = drawdown.min()

#     win_rate = (strategy_ret > 0).mean()

#     return {
#         "total_return": total_return,
#         "annual_return": annual_return,
#         "annual_vol": annual_vol,
#         "sharpe": sharpe,
#         "max_drawdown": max_drawdown,
#         "win_rate": win_rate,
#     }

import numpy as np
import pandas as pd


def run_backtest(
    price_y: pd.Series,
    price_x: pd.Series,
    beta: float,
    positions: pd.Series
) -> pd.DataFrame:
    """
    ペアトレードのポジション系列から日次損益を計算する

    Parameters
    ----------
    price_y : pd.Series
        y銘柄の価格系列
    price_x : pd.Series
        x銘柄の価格系列
    beta : float
        hedge ratio
    positions : pd.Series
        ポジション系列
        1 = long spread
        -1 = short spread
        0 = no position

    Returns
    -------
    pd.DataFrame
        バックテスト結果
    """
    if not np.isfinite(beta):
        raise ValueError(f"beta must be finite, got {beta}")

    df = pd.concat(
        [
            price_y.rename("price_y"),
            price_x.rename("price_x"),
            positions.rename("position"),
        ],
        axis=1
    ).dropna().copy()

    if len(df) < 2:
        raise ValueError("Not enough aligned data after concat/dropna.")

    df["ret_y"] = df["price_y"].pct_change()
    df["ret_x"] = df["price_x"].pct_change()

    # 当日シグナルを翌日に反映
    df["held_position"] = df["position"].shift(1).fillna(0)

    # long spread: +1 のとき y買い / beta*x売り
    # short spread: -1 のとき y売り / beta*x買い
    df["pair_return"] = df["ret_y"] - beta * df["ret_x"]
    df["strategy_return"] = df["held_position"] * df["pair_return"]
    df["strategy_return"] = df["strategy_return"].fillna(0)

    df["equity_curve"] = (1 + df["strategy_return"]).cumprod()

    return df


def calculate_performance(strategy_return: pd.Series) -> dict:
    """
    戦略リターン系列から基本成績を計算する
    """
    strategy_return = strategy_return.dropna()

    if len(strategy_return) == 0:
        return {
            "total_return": np.nan,
            "annual_return": np.nan,
            "annual_vol": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
            "win_rate": np.nan,
        }

    equity = (1 + strategy_return).cumprod()

    total_return = equity.iloc[-1] - 1
    annual_return = equity.iloc[-1] ** (252 / len(strategy_return)) - 1
    annual_vol = strategy_return.std(ddof=0) * np.sqrt(252)

    if annual_vol == 0 or np.isnan(annual_vol):
        sharpe = np.nan
    else:
        sharpe = annual_return / annual_vol

    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = drawdown.min()

    win_rate = (strategy_return > 0).mean()

    return {
        "total_return": float(total_return),
        "annual_return": float(annual_return),
        "annual_vol": float(annual_vol),
        "sharpe": float(sharpe) if not np.isnan(sharpe) else np.nan,
        "max_drawdown": float(max_drawdown),
        "win_rate": float(win_rate),
    }


def create_trade_log(
    bt_df: pd.DataFrame,
    zscore: pd.Series
) -> pd.DataFrame:
    """
    バックテスト結果と zscore からトレードログを作成する

    Parameters
    ----------
    bt_df : pd.DataFrame
        run_backtest() の返り値
        必須列:
        - price_y
        - price_x
        - position
        - held_position
        - strategy_return

    zscore : pd.Series
        spread の zscore 系列

    Returns
    -------
    pd.DataFrame
        1トレードごとのログ
    """
    df = bt_df.copy()
    df = df.join(zscore.rename("zscore"), how="left")

    trades = []
    in_trade = False
    trade = None

    prev_pos = 0

    for dt, row in df.iterrows():
        current_pos = row["held_position"]

        # ===== Entry =====
        if (not in_trade) and (prev_pos == 0) and (current_pos != 0):
            in_trade = True

            trade = {
                "entry_date": dt,
                "side": "long_spread" if current_pos == 1 else "short_spread",
                "entry_price_y": row["price_y"],
                "entry_price_x": row["price_x"],
                "entry_zscore": row["zscore"],
            }

        # ===== Exit =====
        elif in_trade and (prev_pos != 0) and (current_pos == 0):
            if trade is None:
                raise ValueError("trade is None at exit though in_trade=True")
            
            entry_date = trade["entry_date"]

            # entry日から、exit日の前日までが実際の保有区間
            holding_slice = df.loc[entry_date:dt].copy()

            pnl = holding_slice["strategy_return"].sum()
            holding_days = int((holding_slice["held_position"] != 0).sum())

            # exit_reason 推定
            exit_z = row["zscore"]
            exit_reason = "exit"

            if pd.notna(exit_z) and abs(exit_z) > 0.5:
                exit_reason = "stop"

            trade.update({
                "exit_date": dt,
                "exit_price_y": row["price_y"],
                "exit_price_x": row["price_x"],
                "exit_zscore": exit_z,
                "pnl": pnl,
                "holding_days": holding_days,
                "exit_reason": exit_reason,
            })

            trades.append(trade)
            in_trade = False
            trade = None

        prev_pos = current_pos

    # ===== データ末尾でポジションが残っていた場合 =====
    if in_trade and trade is not None:
        last_dt = df.index[-1]
        holding_slice = df.loc[trade["entry_date"]:last_dt].copy()

        pnl = holding_slice["strategy_return"].sum()
        holding_days = int((holding_slice["held_position"] != 0).sum())

        trade.update({
            "exit_date": last_dt,
            "exit_price_y": df.iloc[-1]["price_y"],
            "exit_price_x": df.iloc[-1]["price_x"],
            "exit_zscore": df.iloc[-1]["zscore"],
            "pnl": pnl,
            "holding_days": holding_days,
            "exit_reason": "end_of_data",
        })

        trades.append(trade)

    trade_log = pd.DataFrame(trades)
    return trade_log