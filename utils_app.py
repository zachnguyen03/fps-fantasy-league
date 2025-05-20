import pandas as pd
import numpy as np

csv_path = './database_update_ss3.csv'
# csv_path = './data/sample.csv'
df = pd.read_csv(csv_path)

def get_random_players(df):
    """
    Randomly select half of the players from the DataFrame.
    Returns a new DataFrame containing the randomly selected players.
    """
    n_players = len(df)
    n_selected = np.random.randint(10, n_players)
    return df.sample(n=n_selected, weights=1/(df["Matches"]+0.01))  # random_state for reproducibility

# Postprocess stats
df = df.round(2)
df["Matches"] = df["Wins"] + df["Losses"]
df["KPM"] = (df["TKills"] / df["Matches"]).round(2)
df["DPM"] = (df["TDeaths"] / df["Matches"]).round(2)
df["APM"] = (df["TAssists"] / df["Matches"]).round(2)
df["K/D"] = (df["TKills"] / df["TDeaths"]).round(2)
df["ADR"] = (df["TADR"] / df["Matches"]).round(2)
df["Rating"] = 0.65 * df["K/D"] + 0.024 * df["KPM"] + 0.016 * df["APM"] - 0.025 * df["DPM"] + 0.0035 * df["ADR"]
df["Rating"] = df["Rating"].round(2)
df = df.fillna(0)
df["ELO"] = df["ELO"].round().astype(int)
df = df.sort_values('ELO', ascending=False)

online_df = get_random_players(df)

global_context = {
    "database": df,
    "database_path": csv_path,
    "online_df": online_df
}

# 100T Kyedae,214 anhster,GEN lakia,FNC chronicle,DSG Juicy
# EDG s1mon,TLN primmie,TL jamppi,SEN Tenz,C9 xeppaa