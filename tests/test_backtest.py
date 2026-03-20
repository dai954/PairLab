from data.data_loader import load_test_pair
from research.spread_model import fit_ols_spread, calculate_zscore
from backtest.backtest_engine import (
    generate_positions,
    calculate_pair_returns,
    calculate_performance,
)

# 1. ペア価格データ
price_y, price_x = load_test_pair()

# 2. spreadモデル作成
model = fit_ols_spread(price_y, price_x)

alpha = model["alpha"]
beta = model["beta"]
spread = model["spread"]

# 3. zscore作成
zscore = calculate_zscore(spread, window=20)

# 4. position作成
position = generate_positions(
    zscore,
    entry_threshold=2.0,
    exit_threshold=0.5
)

# 5. バックテスト
bt_df = calculate_pair_returns(
    price_y=price_y,
    price_x=price_x,
    beta=beta,
    position=position
)

# 6. 成績
perf = calculate_performance(bt_df["strategy_ret"])

print(bt_df[["position", "position_lag", "strategy_ret", "equity_curve"]].tail(20))
print(perf)