from universe.universe import load_universe
from data.data_loader import load_price_data
from research.pair_finder import find_high_corr_pairs
from research.cointegration import filter_cointegrated_pairs
from research.spread_model import build_pair_model


def main():
    # 1. 価格データ読み込み
    tickers = load_universe()
    price_df = load_price_data(tickers)

    # 2. 相関フィルター
    corr_pairs = find_high_corr_pairs(price_df)

    print(f"高相関ペア数: {len(corr_pairs)}")

    # 3. cointegration検定
    coint_pairs = filter_cointegrated_pairs(price_df, corr_pairs)

    print(f"cointegration通過ペア数: {len(coint_pairs)}")

    # 4. モデル構築
    pair_models = []

    for item in coint_pairs:
        s1, s2 = item["pair"]

        model = build_pair_model(price_df, s1, s2)

        model["corr"] = item["corr"]
        model["pvalue"] = item["pvalue"]
        pair_models.append(model)

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


if __name__ == "__main__":
    main()