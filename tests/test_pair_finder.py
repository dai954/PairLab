from universe.universe import load_universe
from data.data_loader import load_price_data
from research.pair_finder import find_high_corr_pairs

def main():
    tickers = load_universe()
    price_df = load_price_data(tickers)
    pairs = find_high_corr_pairs(price_df, threshold=0.9)
    
    print("抽出ペア一覧:")
    for s1, s2, corr in pairs:
        print(f"{s1} - {s2}: {corr:.2f}")

if __name__ == "__main__":
    main()