import gradio as gr
import numpy as np
import json

import pandas as pd
from utils_app import global_context

import os


def init_database(df):
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
    df.sort_values('Rating', ascending=False)
    return df

def update_database():
    df_new = df.round(2)
    df_new["Matches"] = df["Wins"] + df["Losses"]
    df_new["KPM"] = (df["TKills"] / df["Matches"]).round(2)
    df_new["DPM"] = (df["TDeaths"] / df["Matches"]).round(2)
    df_new["APM"] = (df["TAssists"] / df["Matches"]).round(2)
    df_new["K/D"] = (df["TKills"] / df["TDeaths"]).round(2)
    df_new["ADR"] = (df["TADR"] / df["Matches"]).round(2)
    df_new["Rating"] = (0.65 * df_new["K/D"] + 0.024 * df_new["KPM"] + 0.016 * df_new["APM"] - 0.025 * df_new["DPM"] + 0.0035 * df_new["ADR"]).round(2)
    # df_new = df_new.round(2)
    df_new = df_new.fillna(0)
    df_new = df_new.sort_values('ELO', ascending=False)
    df_new = df_new.round(2)
    top_1 = gr.Label(f'{df_new.iloc[0]["Name"]} - {df_new.iloc[0]["ELO"]} ELO', label="Top 1")
    top_2 = gr.Label(f'{df_new.iloc[1]["Name"]} - {df_new.iloc[1]["ELO"]} ELO', label="Top 2")
    top_3 = gr.Label(f'{df_new.iloc[2]["Name"]} - {df_new.iloc[2]["ELO"]} ELO', label="Top 3")
    database = gr.DataFrame(df_new, label="VCT Superserver Season 2")
    return database, top_1, top_2, top_3

def init_game(t1p1, t1p2, t1p3, t1p4, t1p5, t2p1, t2p2, t2p3, t2p4, t2p5):
    players_1 = [t1p1, t1p2, t1p3, t1p4, t1p5]
    players_2 = [t2p1, t2p2, t2p3, t2p4, t2p5]
    # players_1 = lineup_1.split(",")
    # players_2 = lineup_2.split(",")
    df_1 = df.loc[df['Name'].isin(players_1)]
    df_2 = df.loc[df['Name'].isin(players_2)]
    ELO_1 = df_1["ELO"].sum()
    ELO_2 = df_2["ELO"].sum()
    elo_diff = gr.Number(label="ELO difference", value=ELO_1-ELO_2, visible=True)
    t1_gain = gr.Number(label="Team 1 gain", value=25-min(25, (ELO_1-ELO_2)//50), visible=True)
    t2_gain = gr.Number(label="Team 2 gain", value=25+min(25, (ELO_1-ELO_2)//50), visible=True)
    win_team = gr.Radio(["Team 1", "Team 2"], label="Winning Team", visible=True, interactive=True)
    team_1 = gr.Dataframe(df_1[["Name", "Matches", "Rating", "ELO"]], label="Team 1", interactive=False, visible=True)
    team_2 = gr.Dataframe(df_2[["Name", "Matches", "Rating", "ELO"]], label="Team 2", interactive=False, visible=True)
    return team_1, team_2, elo_diff, t1_gain, t2_gain, win_team


def get_rating(kd, kpm, apm, dpm, adr):
    return round(0.65*kd + 0.024*kpm + 0.016*apm - 0.025*dpm + 0.0035*adr,2)


def save_database_csv():
    df.to_csv(global_context["database_path"], index=False)
    return True

def save_match_history(team_1_result, team_2_result):
    os.makedirs('./match_history', exist_ok=True)
    match_num = len(os.listdir('./match_history'))
    os.makedirs(f'./match_history/match_{match_num+1}', exist_ok=True)
    team_1_result.to_csv(f'./match_history/match_{match_num+1}/t1.csv', index=False)
    team_2_result.to_csv(f'./match_history/match_{match_num+1}/t2.csv', index=False)


def submit_match(result_1, result_2, t1_gain, t2_gain, win_team):
    players_1 = result_1["Name"].to_list()
    players_2 = result_2["Name"].to_list()
    average_elo = (df.loc[df["Name"].isin(players_1)]["ELO"].sum() + df.loc[df["Name"].isin(players_2)]["ELO"].sum())//10
    print("Average elo: ", average_elo)
    if win_team == "Team 1":
        elo = t1_gain
    else:
        elo = t2_gain
    for player in players_1:
        # print(df.loc[df["Name"] == player])
        df.loc[df["Name"] == player, 'Matches'] += 1
        df.loc[df["Name"] == player, "Wins"] += 1
        df.loc[df["Name"] == player, "TKills"] += int(result_1.loc[result_1["Name"] == player]["K"])
        df.loc[df["Name"] == player, "TDeaths"] += int(result_1.loc[result_1["Name"] == player]["D"])
        df.loc[df["Name"] == player, "TAssists"] += int(result_1.loc[result_1["Name"] == player]["A"])
        df.loc[df["Name"] == player, "TADR"] += int(result_1.loc[result_1["Name"] == player]["ADR"])
        df.loc[df["Name"] == player, "MVP"] += int(result_1.loc[result_1["Name"] == player]["MVP"])
        rating = get_rating(int(result_1.loc[result_1["Name"] == player]["K"])/int(result_1.loc[result_1["Name"] == player]["D"]),
                            int(result_1.loc[result_1["Name"] == player]["K"]),
                            int(result_1.loc[result_1["Name"] == player]["A"]),
                            int(result_1.loc[result_1["Name"] == player]["D"]),
                            int(result_1.loc[result_1["Name"] == player]["ADR"]))
        print(f"ELO difference for {player}:  {int(df.loc[df['Name'] == player, 'ELO'] - average_elo)}")
        print(f"Rating for {player}: {rating}")
        print(f"ELO coeff: ", int((df.loc[df["Name"] == player, "ELO"] - average_elo) * 0.05))
        print("ELO gain/loss: ", int(int(elo) + min(15, int(rating * 5)) - int((df.loc[df["Name"] == player, "ELO"] - average_elo) * 0.03) + int(result_1.loc[result_1["Name"] == player, "MVP"]) * 10))
        df.loc[df["Name"] == player, "ELO"] += int(int(elo) + min(15, int(rating * 5)) - int((df.loc[df["Name"] == player, "ELO"] - average_elo) * 0.03) + int(result_1.loc[result_1["Name"] == player, "MVP"]) * 10)

    for player in players_2:
        print(df.loc[df["Name"] == player])
        df.loc[df["Name"] == player, "Matches"] += 1
        df.loc[df["Name"] == player, "Losses"] += 1
        df.loc[df["Name"] == player, "TKills"] += int(result_2.loc[result_2["Name"] == player]["K"])
        df.loc[df["Name"] == player, "TDeaths"] += int(result_2.loc[result_2["Name"] == player]["D"])
        df.loc[df["Name"] == player, "TAssists"] += int(result_2.loc[result_2["Name"] == player]["A"])
        df.loc[df["Name"] == player, "TADR"] += int(result_2.loc[result_2["Name"] == player]["ADR"])
        rating = get_rating(int(result_2.loc[result_2["Name"] == player]["K"])/int(result_2.loc[result_2["Name"] == player]["D"]),
                            int(result_2.loc[result_2["Name"] == player]["K"]),
                            int(result_2.loc[result_2["Name"] == player]["A"]),
                            int(result_2.loc[result_2["Name"] == player]["D"]),
                            int(result_2.loc[result_2["Name"] == player]["ADR"]))
        print(f"ELO difference for {player}:  {int(df.loc[df['Name'] == player, 'ELO'] - average_elo)}")
        print(f"Rating for {player}: {rating}")
        print(f"ELO coeff: ", int((df.loc[df["Name"] == player, "ELO"] - average_elo) * 0.05))
        print("ELO gain/loss: ", (int(elo) + max(0, (10 - int(rating * 10))) + int((df.loc[df["Name"] == player, "ELO"] - average_elo) * 0.03)))
        df.loc[df["Name"] == player, "ELO"] -= (int(elo) + max(0, (10 - int(rating * 10))) + int((df.loc[df["Name"] == player, "ELO"] - average_elo) * 0.03))
    database, top_1, top_2, top_3 = update_database()
    return database, top_1, top_2, top_3
    

if __name__ == '__main__':
    with gr.Blocks(theme=gr.themes.Soft()) as app:
        df = global_context["database"]
        print(df.columns)
        with gr.Tab("Database"):
            with gr.Row():
                gr.Markdown("Welcome to Valo:GO Fantasy League - Season 1")
                update_button = gr.Button(value="Update", scale=0)
                save_button = gr.Button(value="Save Database", scale=0)
            with gr.Row():
                top_1 = gr.Label(f'{df.iloc[0]["Name"]} - {df.iloc[0]["ELO"]} ELO', label="Top 1")
                top_2 = gr.Label(f'{df.iloc[1]["Name"]} - {df.iloc[1]["ELO"]} ELO', label="Top 2")
                top_3 = gr.Label(f'{df.iloc[2]["Name"]} - {df.iloc[2]["ELO"]} ELO', label="Top 3")
            with gr.Row():
                gr.ScatterPlot(df, x="ELO", y="Rating", title="ELO and Rating distribution", color="Matches", x_lim=[df["ELO"].min()-50, df["ELO"].max()+50], y_lim=[0,2.5])
            database = gr.DataFrame(df, label="VCT Superserver Season 2")
        
        save_button.click(save_database_csv, None, None)
        update_button.click(update_database, None, [database, top_1, top_2, top_3])

        with gr.Tab("Live game"):
            with gr.Row():
                create_button = gr.Button(value="Create game", scale=0)
                submit_button = gr.Button(value="Submit", scale=0)
                save_button = gr.Button(value="Save match", scale=0)
            with gr.Row():
                gr.Markdown("Team 1")
                t1p1 = gr.Dropdown(sorted(df["Name"].to_list()), label="P1")
                t1p2 = gr.Dropdown(sorted(df["Name"].to_list()), label="P2")
                t1p3 = gr.Dropdown(sorted(df["Name"].to_list()), label="P3")
                t1p4 = gr.Dropdown(sorted(df["Name"].to_list()), label="P4")
                t1p5 = gr.Dropdown(sorted(df["Name"].to_list()), label="P5")
            with gr.Row():
                gr.Markdown("Team 2")
                t2p1 = gr.Dropdown(sorted(df["Name"].to_list()), label="P1")
                t2p2 = gr.Dropdown(sorted(df["Name"].to_list()), label="P2")
                t2p3 = gr.Dropdown(sorted(df["Name"].to_list()), label="P3")
                t2p4 = gr.Dropdown(sorted(df["Name"].to_list()), label="P4")
                t2p5 = gr.Dropdown(sorted(df["Name"].to_list()), label="P5")
            with gr.Row():
                team_1 = gr.Dataframe(visible=False, scale=2)
                with gr.Column():
                    elo_diff = gr.Number(label="ELO difference",
                                          value=None,
                                          interactive=False,
                                          visible=False)
                    with gr.Row():
                        t1_gain = gr.Number(label="Team 1 gain",
                                            value=None,
                                            interactive=False, visible=False)
                        t2_gain = gr.Number(label="Team 2 gain",
                                            value=None,
                                            interactive=False,
                                            visible=False)
                    win_team = gr.Radio(["Team 1", "Team 2"], label="Winning Team", visible=False)
                team_2 = gr.Dataframe(visible=False, scale=2)
            with gr.Row():
                team_1_result = gr.Dataframe(headers=["Name", "K", "D", "A", "ADR", "MVP"],
                                             datatype=["str", "number", "number", "number", "number", "number"],
                                             row_count=5,
                                             interactive=True,
                                             label="Winning Team",
                                            )
                team_2_result = gr.Dataframe(headers=["Name", "K", "D", "A", "ADR", "MVP"],
                                             datatype=["str", "number", "number", "number", "number", "number"],
                                             row_count=5,
                                             interactive=True,
                                             label="Losing Team",
                                            )
        with gr.Tab("Statistics"):
            gr.ScatterPlot(df, x="ELO", y="Rating", color="Matches", x_lim=[df["ELO"].min()-50, df["ELO"].max()+50], y_lim=[0,2.5])
            # gr.BarPlot(df, x="Matches", y="Wins", y_aggregate="sum", x_bin=1)
        create_button.click(init_game, [t1p1, t1p2, t1p3, t1p4, t1p5, t2p1, t2p2, t2p3, t2p4, t2p5], [team_1, team_2, elo_diff, t1_gain, t2_gain, win_team])
        submit_button.click(submit_match, [team_1_result, team_2_result, t1_gain, t2_gain, win_team], [database, top_1, top_2, top_3])
        save_button.click(save_match_history, [team_1_result, team_2_result], None)
        

    app.launch()
 