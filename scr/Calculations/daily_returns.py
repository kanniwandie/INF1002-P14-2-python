"""
    Compute the single-day percentage return at a given row index.

    Formula:
        r_t (%) = ((P_t - P_{t-1}) / P_{t-1}) * 100
      where P_t is df.loc[index, "Close"] and P_{t-1} is df.loc[index-1, "Close"].

    Args:
        df (pd.DataFrame): Price DataFrame containing at least a "Close" column.
                           Rows should be in chronological order.
        index (int): Row index for day t (must be >= 1 so that t-1 exists).

    Returns:
        float: Daily return for day t expressed in percent.

    Notes:
        - Will raise if index == 0 (no previous day) or if "Close" is missing.
        - Assumes previous close (P_{t-1}) is nonzero.
"""

def dr_calc(df, index):
    dc = float(df.loc[index, "Close"])
    pc = float(df.loc[index-1,"Close"])
    daily_return = ((dc-pc)/pc)*100
    return daily_return