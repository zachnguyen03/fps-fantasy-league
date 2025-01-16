import gradio as gr
import numpy as np
import json

import pandas as pd
from utils_app import global_context


def init_app(json_path):
    # data = json.load(json_path)
    # with gr.Blocks as demo:
    pass

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
    df.sort_values('Rating')
    return df

def update_database():
    return gr.DataFrame(df, label="VCT Superserver Season 2")

def init_game(lineup_1, lineup_2):
    players_1 = lineup_1.split(",")
    players_2 = lineup_2.split(",")
    df_1 = df.loc[df['Name'].isin(players_1)]
    df_2 = df.loc[df['Name'].isin(players_2)]
    team_1 = gr.Dataframe(df_1, label="Team 1", interactive=False, visible=True)
    team_2 = gr.Dataframe(df_2, label="Team 2", interactive=False, visible=True)
    return team_1, team_2

def save_database_csv():
    df.to_csv(global_context["database_path"])
    return True

def submit_match(lineup_1, lineup_2, result_1, result_2):
    players_1 = lineup_1.split(",")
    players_2 = lineup_2.split(",")
    for player in players_1:
        print(df.loc[df["Name"] == player])
        df.loc[df["Name"] == player, 'Matches'] += 1
        df.loc[df["Name"] == player, "Wins"] += 1
        df.loc[df["Name"] == player, "TKills"] += int(result_1.loc[result_1["Name"] == player]["K"])
        df.loc[df["Name"] == player, "TDeaths"] += int(result_1.loc[result_1["Name"] == player]["D"])
        df.loc[df["Name"] == player, "TAssists"] += int(result_1.loc[result_1["Name"] == player]["A"])
        df.loc[df["Name"] == player, "TADR"] += int(result_1.loc[result_1["Name"] == player]["ADR"])

    for player in players_2:
        print(df.loc[df["Name"] == player])
        df.loc[df["Name"] == player, "Matches"] += 1
        df.loc[df["Name"] == player, "Losses"] += 1
        df.loc[df["Name"] == player, "TKills"] += int(result_2.loc[result_2["Name"] == player]["K"])
        df.loc[df["Name"] == player, "TDeaths"] += int(result_2.loc[result_2["Name"] == player]["D"])
        df.loc[df["Name"] == player, "TAssists"] += int(result_2.loc[result_2["Name"] == player]["A"])
        df.loc[df["Name"] == player, "TADR"] += int(result_2.loc[result_2["Name"] == player]["ADR"])
    
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
    df.sort_values('Rating')

    return gr.Dataframe(df, label="VCT Superserver Season 2")

if __name__ == '__main__':
    # csv_path = './database_compressed.csv'
    # df = pd.read_csv(csv_path)
    # # Postprocess stats
    
    # df = df.round(2)
    # df["Matches"] = df["Wins"] + df["Losses"]
    # df["KPM"] = (df["TKills"] / df["Matches"]).round(2)
    # df["DPM"] = (df["TDeaths"] / df["Matches"]).round(2)
    # df["APM"] = (df["TAssists"] / df["Matches"]).round(2)
    # df["K/D"] = (df["TKills"] / df["TDeaths"]).round(2)
    # df["ADR"] = (df["TADR"] / df["Matches"]).round(2)
    # df["Rating"] = 0.65 * df["K/D"] + 0.024 * df["KPM"] + 0.016 * df["APM"] - 0.025 * df["DPM"] + 0.0035 * df["ADR"]
    # df["Rating"] = df["Rating"].round(2)
    # df = df.fillna(0)
    # df.sort_values('Rating')

    # styler = df.style.highlight_max(color = 'lightgreen', axis = 0)
    # init_app(json_path)
    with gr.Blocks() as app:
        df = global_context["database"]
        print(df)
        with gr.Tab("Database"):
            with gr.Row():
                gr.Markdown("Welcome to Valorant Superserver - Season 2")
                update_button = gr.Button(value="Update", scale=0)
                save_button = gr.Button(value="Save Database", scale=0)
            with gr.Row():
                gr.Label(df.iloc[0]["Name"], label="Best Rating")
                gr.Label(df.iloc[-1]["Name"], label="Worst Rating")
            database = gr.DataFrame(df, label="VCT Superserver Season 2")
        
        save_button.click(save_database_csv, None, None)
        update_button.click(update_database, None, database)

        with gr.Tab("Live game"):
            with gr.Row():
                gr.Markdown("There is no live game")
                create_button = gr.Button(value="Create game", scale=0)
                submit_button = gr.Button(value="Submit", scale=0)
            lineup_1 = gr.Textbox(label="Team 1 Players",
                                  value=None,
                                  interactive=True)
            lineup_2 = gr.Textbox(label="Team 2 Players",
                                  value=None,
                                  interactive=True)
            team_1 = gr.Dataframe(visible=False)
            team_2 = gr.Dataframe(visible=False)
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
            gr.DataFrame(df, label="VCT Superserver Season 2")
        # print(df.to_json(orient="records"))
        create_button.click(init_game, [lineup_1, lineup_2], [team_1, team_2])
        submit_button.click(submit_match, [lineup_1, lineup_2, team_1_result, team_2_result], database)

    app.launch()
