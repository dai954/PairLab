from universe.universe import load_universe_df, build_industry_map

universe_df = load_universe_df()
industry_map = build_industry_map(universe_df)

print(universe_df)
print(type(universe_df))
print("########################")
print(industry_map)
print(type(industry_map))