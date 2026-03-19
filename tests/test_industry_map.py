from universe.universe import load_universe_df, build_industry_map

df = load_universe_df()
industry_map = build_industry_map(df, industry_col="33業種区分")

print(list(industry_map.items())[:5])
print(industry_map.get("7203.T"))
print(industry_map.get("6758.T"))