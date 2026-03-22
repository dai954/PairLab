from data.data_loader import load_test_pair
from research.spread_model import fit_ols_spread, calculate_zscore
from backtest.backtest_engine import (
    run_backtest,
    calculate_performance,
)
from strategy.pairs_signal import generate_positions

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
positions = generate_positions(
    zscore,
    entry_threshold=2.0,
    exit_threshold=0.5,
    stop_threshold=3.5
)

# 5. バックテスト
bt_df = run_backtest(
    price_y=price_y,
    price_x=price_x,
    beta=beta,
    positions=positions
)

# 6. 成績
perf = calculate_performance(bt_df["strategy_return"])

print("##### run_backtest tail(20)#####")
print(bt_df[["price_y", "price_x","position", "held_position", "strategy_return", "equity_curve"]].tail(20))
print("##### calculate_performance #####")
print(perf)