
def filter_pairs_by_industry(pairs, industry_map):
    """
    同じ業界のペアだけ残す

    Parameters
    ----------
    pairs : list of tuple
        [(s1, s2, corr), ...]
    industry_map : dict
        {"7203.T": "輸送用機器", ...}

    Returns
    -------
    list of tuple
        同業界ペアのみ
    """
    filtered_pairs = []

    for s1, s2, corr in pairs:
        industry1 = industry_map.get(s1)
        industry2 = industry_map.get(s2)

        # 業界情報がない銘柄は除外
        if industry1 is None or industry2 is None:
            continue

        if industry1 == industry2:
            filtered_pairs.append((s1, s2, corr))

    return filtered_pairs

def group_tickers_by_industry(tickers, industry_map):
    """
    銘柄を業界ごとにグループ分けする

    Parameters
    ----------
    tickers : list
        ["7203.T", "6758.T", ...]
    industry_map : dict
        {"7203.T": "輸送用機器", ...}

    Returns
    -------
    dict
        {
            "輸送用機器": ["7203.T", "7267.T"],
            "電気機器": ["6758.T", "6501.T"]
        }
    """
    groups = {}

    for t in tickers:
        industry = industry_map.get(t)

        if industry is None:
            continue

        if industry not in groups:
            groups[industry] = []

        groups[industry].append(t)

    return groups