import pandas as pd

csv_path = './database_compressed.csv'
df = pd.read_csv(csv_path)

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
df = df.sort_values('ELO', ascending=False)

global_context = {
    "database": df,
    "database_path": csv_path
}

# 100T Kyedae,214 anhster,GEN lakia,FNC chronicle,DSG Juicy
# EDG s1mon,TLN primmie,TL jamppi,SEN Tenz,C9 xeppaa