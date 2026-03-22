from config.settings import MAX_TICKERS, START_DATE
from universe.universe import load_universe_tickers, load_universe_df, build_industry_map
from data.data_loader import load_price_data
from research.pair_finder import find_high_corr_pairs, find_corr_pairs_within_industries
from research.industry_filter import filter_pairs_by_industry, group_tickers_by_industry
from research.cointegration import filter_cointegrated_pairs
from research.spread_model import build_pair_model
from research.parameter_search import run_parameter_search
from strategy.pairs_signal import generate_positions, calculate_zscore
from backtest.backtest_engine import run_backtest, calculate_performance, create_trade_log


def main():
    # 1. 価格データ読み込み
    tickers = load_universe_tickers()
    # テスト用制限
    tickers = tickers[:MAX_TICKERS]
    price_df = load_price_data(tickers, START_DATE)

    # 2. 相関フィルター
    # corr_pairs = find_high_corr_pairs(price_df)

    # print(f"高相関ペア数: {len(corr_pairs)}")
    # print("===== 高相関ペア 上位20件 =====")
    # for s1, s2, corr in corr_pairs[:20]:
    #     print(f"{s1} - {s2} : corr={corr:.4f}")

    # 業界情報読み込み
    universe_df = load_universe_df()
    industry_map = build_industry_map(universe_df, industry_col="33業種区分")

    # 業界フィルター
    # industry_pairs = filter_pairs_by_industry(corr_pairs, industry_map)
    # print(f"業界フィルター通過ペア数: {len(industry_pairs)}")
    
    # price_dfでダウンロードされた分のtickerだけに絞る
    available_tickers = price_df.columns.tolist()
    industry_groups = group_tickers_by_industry(available_tickers, industry_map)

    all_corr_pairs = find_corr_pairs_within_industries(
    price_df,
    industry_groups
    )

    print(f"全業界合計ペア数: {len(all_corr_pairs)}")

    # 3. cointegration検定
    coint_pairs = filter_cointegrated_pairs(price_df, all_corr_pairs)

    print(f"cointegration通過ペア数: {len(coint_pairs)}")

    # 4. モデル構築
    pair_models = []

    for item in coint_pairs:
        s1, s2 = item["pair"]

        model = build_pair_model(price_df, s1, s2)

        model["corr"] = item["corr"]
        model["pvalue"] = item["pvalue"]
        pair_models.append(model)

    if len(pair_models) == 0:
        print("pair model を構築できませんでした")
        return

    # 5. 結果表示
    print("===== 上位ペア =====")
    for model in pair_models[:10]:
        print(
            model["pair"],
            f"corr={model['corr']:.3f}",
            f"pvalue={model['pvalue']:.4f}",
            f"half_life={model['half_life']:.2f}",
            f"beta={model['beta']:.4f}"
        )

    # 7. まずは先頭1ペアを対象に詳細検証
    target_model = pair_models[0]
    s1, s2 = target_model["pair"]
    beta = target_model["beta"]
    spread = target_model["spread"]

    print("\n===== 対象ペア詳細 =====")
    print(
        target_model["pair"],
        f"corr={target_model['corr']:.3f}",
        f"pvalue={target_model['pvalue']:.4f}",
        f"half_life={target_model['half_life']:.2f}",
        f"beta={target_model['beta']:.4f}"
    )

    # 8. zscore計算
    zscore = calculate_zscore(spread, window=20)

    # 9. positions生成
    positions = generate_positions(
        zscore=zscore,
        entry_threshold=2.0,
        exit_threshold=0.5,
        stop_threshold=3.5,
    )

    # 10. backtest実行
    bt = run_backtest(
        price_y=price_df[s1],
        price_x=price_df[s2],
        beta=beta,
        positions=positions,
    )

    # 11. performance計算
    metrics = calculate_performance(bt["strategy_return"])

    print("\n===== Backtest Performance =====")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    print("\n===== Backtest tail =====")
    print(
        bt[["price_y", "price_x", "position", "held_position", "pair_return", "strategy_return", "equity_curve"]].tail(10)
    )

    # 12. trade log 作成
    trade_log = create_trade_log(bt, zscore)

    print("\n===== Trade Log =====")
    print(trade_log.head(20))

    print(f"\nトレード数: {len(trade_log)}")

    if len(trade_log) > 0:
        print("\n===== Trade Log Summary =====")
        print("平均損益:", trade_log["pnl"].mean())
        print("勝率:", (trade_log["pnl"] > 0).mean())
        print("平均保有日数:", trade_log["holding_days"].mean())
        print("\nExit reason 内訳:")
        print(trade_log["exit_reason"].value_counts())

    # ===== パラメータ比較 =====
    result_df = run_parameter_search(
        price_df=price_df,
        s1=s1,
        s2=s2,
        beta=beta,
        spread=spread,
        entry_list=[1.5, 2.0, 2.5],
        exit_list=[0.3, 0.5, 1.0],
        window=20,
        stop_threshold=3.5,
    )

    display_df = result_df.copy()
    round_cols = [
        "total_return",
        "annual_return",
        "annual_vol",
        "sharpe",
        "max_drawdown",
        "daily_win_rate",
        "trade_win_rate",
        "avg_holding_days",
    ]
    for col in round_cols:
        display_df[col] = display_df[col].round(4)

    print("\n===== Parameter Comparison =====")
    print(
        display_df.sort_values(
            by=["sharpe", "total_return"],
            ascending=[False, False]
        ).to_string(index=False)
    )



if __name__ == "__main__":
    main()