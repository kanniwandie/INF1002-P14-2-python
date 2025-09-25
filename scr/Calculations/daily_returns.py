def dr_calc(df, index):
    dc = float(df.loc[index, "Close"])
    pc = float(df.loc[index-1,"Close"])
    daily_return = ((dc-pc)/pc)*100
    return daily_return
