from flask import Flask, render_template, jsonify, request, send_from_directory
import numpy as np
from random import sample
import pandas as pd
import os
import base64
import database as db
import sqlite3
import cv2
import easyocr
from PIL import Image
import io
import re

app = Flask(__name__)

# Fix for Pillow 10+ compatibility with EasyOCR
# Pillow 10.0.0+ removed Image.ANTIALIAS, but EasyOCR still uses it
if not hasattr(Image, 'ANTIALIAS'):
    # Map ANTIALIAS to LANCZOS (the modern equivalent)
    Image.ANTIALIAS = Image.LANCZOS

# Initialize EasyOCR reader (lazy initialization to avoid loading on import)
ocr_reader = None
OCR_AVAILABLE = False

def init_ocr():
    """Initialize OCR reader if available"""
    global ocr_reader, OCR_AVAILABLE
    if ocr_reader is None:
        try:
            ocr_reader = easyocr.Reader(['en'], gpu=True)
            OCR_AVAILABLE = True
            print("EasyOCR initialized successfully")
        except Exception as e:
            print(f"Warning: EasyOCR not available: {e}")
            print("Install with: pip install easyocr")
            OCR_AVAILABLE = False
    return OCR_AVAILABLE

# Serve static assets
@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('assets', filename)

# Initialize database
if not db.database_exists():
    csv_path = './data/vct_ss4.csv'
    if not os.path.exists(csv_path):
        csv_path = './vct_ss4.csv'
    db.init_database_from_csv(csv_path)

# Migrate database to add new columns if needed
try:
    import database_migration
    database_migration.migrate_database()
except Exception as e:
    print(f"Warning: Database migration failed: {e}")

# Load initial data
df = db.get_all_players()
df = df.round(2)
df["Matches"] = df["Wins"] + df["Losses"]
df["KPM"] = (df["TKills"] / df["Matches"]).round(2)
df["DPM"] = (df["TDeaths"] / df["Matches"]).round(2)
df["APM"] = (df["TAssists"] / df["Matches"]).round(2)
df["K/D"] = (df["TKills"] / df["TDeaths"]).round(2)
df["ADR"] = (df["TADR"] / df["Matches"]).round(2)
df["Rating"] = 0.28 * df["K/D"] + 0.02 * df["KPM"] + 0.006 * df["APM"] + 0.0058 * df["ADR"]
df["Rating"] = df["Rating"].round(2)

# Ensure new columns exist
if "KPR" not in df.columns:
    df["KPR"] = 0.0
if "DPR" not in df.columns:
    df["DPR"] = 0.0
if "APR" not in df.columns:
    df["APR"] = 0.0
if "MatchHistory" not in df.columns:
    df["MatchHistory"] = ""

df = df.fillna(0)
df["ELO"] = df["ELO"].round().astype(int)
df = df.sort_values('ELO', ascending=False)

# Global context - determine CSV path
csv_path = './data/vct_ss4.csv'
if not os.path.exists(csv_path):
    csv_path = './vct_ss4.csv'

global_context = {
    "database": df,
    "database_path": csv_path,
}

def get_rank(elo):
    """Determine rank based on ELO"""
    if elo < 1000:
        return "silver"
    elif elo < 1100:
        return "gold"
    elif elo < 1300:
        return "diamond"
    elif elo < 1500:
        return "gosu"
    else:
        return "worthy"

def get_rank_icon_base64(rank):
    """Get base64 encoded SVG icon for rank"""
    icon_path = f"assets/logos/{rank}.svg"
    try:
        with open(icon_path, 'rb') as f:
            svg_data = f.read()
            b64_data = base64.b64encode(svg_data).decode('utf-8')
            return f"data:image/svg+xml;base64,{b64_data}"
    except Exception as e:
        print(f"Error loading icon for {rank}: {e}")
        return ""

def get_random_players(df):
    """Randomly select players from the DataFrame"""
    n_players = len(df)
    n_selected = np.random.randint(10, n_players//2)
    # return df.sample(n=n_selected, weights=1/(df["Matches"]+0.01))
    return df.sample(n=n_selected)

def get_rating(kd, kpm, apm, dpm, adr):
    return round(0.65*kd + 0.024*kpm + 0.016*apm - 0.025*dpm + 0.0035*adr, 2)

def update_database_stats():
    """Update database statistics"""
    df_source = global_context["database"]
    df_new = df_source.round(2)
    df_new["Matches"] = df_source["Wins"] + df_source["Losses"]
    df_new["KPM"] = (df_source["TKills"] / df_new["Matches"]).round(2)
    df_new["DPM"] = (df_source["TDeaths"] / df_new["Matches"]).round(2)
    df_new["APM"] = (df_source["TAssists"] / df_new["Matches"]).round(2)
    df_new["K/D"] = (df_source["TKills"] / df_source["TDeaths"]).round(2)
    df_new["ADR"] = (df_source["TADR"] / df_new["Matches"]).round(2)
    df_new["Rating"] = (0.28 * df_new["K/D"] + 0.02 * df_new["KPM"] + 0.006 * df_new["APM"] + 0.0058 * df_new["ADR"]).round(2)
    
    # Ensure new columns exist
    if "KPR" not in df_new.columns:
        df_new["KPR"] = 0.0
    if "DPR" not in df_new.columns:
        df_new["DPR"] = 0.0
    if "APR" not in df_new.columns:
        df_new["APR"] = 0.0
    if "MatchHistory" not in df_new.columns:
        df_new["MatchHistory"] = ""
    
    df_new = df_new.fillna(0)
    df_new = df_new.sort_values('ELO', ascending=False)
    df_new = df_new.round(2)
    global_context["database"] = df_new
    db.bulk_update_from_dataframe(df_new)
    return df_new

@app.route('/', methods=['GET'])
def index():
    """Main page"""
    df_current = global_context["database"]
    online_df = get_random_players(df_current)
    top_3 = df_current.head(3)
    
    # Add rank icons to top 3
    top_3_list = []
    for _, row in top_3.iterrows():
        rank = get_rank(row["ELO"])
        icon_data = get_rank_icon_base64(rank)
        top_3_list.append({
            "Name": row["Name"],
            "ELO": int(row["ELO"]),
            "rank_icon": icon_data
        })
    return render_template('index.html', 
                         top_3=top_3_list,
                         online_players=online_df["Name"].tolist())

@app.route('/', methods=['POST'])
def index_post():
    """Handle POST requests to root - silently ignore to prevent 405 spam"""
    # Silently return 200 to prevent browser retries
    return '', 200

@app.route('/api/reset-database', methods=['POST'])
def reset_database():
    """Reset all player stats to default values"""
    try:
        conn = sqlite3.connect(db.DB_PATH)
        cursor = conn.cursor()
        
        # Reset all player stats to default values
        cursor.execute('''
            UPDATE players 
            SET 
                Wins = 0,
                Losses = 0,
                TKills = 0,
                TDeaths = 0,
                TAssists = 0,
                TADR = 0,
                MVP = 0,
                Matches = 0,
                KPM = 0.0,
                DPM = 0.0,
                APM = 0.0,
                "K/D" = 0.0,
                ADR = 0.0,
                Rating = 0.0,
                ELO = 1000,
                KPR = 0.0,
                DPR = 0.0,
                APR = 0.0,
                MatchHistory = ''
        ''')
        
        conn.commit()
        conn.close()
        
        # Reload database
        df = db.get_all_players()
        df = df.round(2)
        df["Matches"] = df["Wins"] + df["Losses"]
        # Handle division by zero
        df["KPM"] = (df["TKills"] / df["Matches"].replace(0, 1)).round(2)
        df["DPM"] = (df["TDeaths"] / df["Matches"].replace(0, 1)).round(2)
        df["APM"] = (df["TAssists"] / df["Matches"].replace(0, 1)).round(2)
        df["K/D"] = (df["TKills"] / df["TDeaths"].replace(0, 1)).round(2)
        df["ADR"] = (df["TADR"] / df["Matches"].replace(0, 1)).round(2)
        df["Rating"] = 0.28 * df["K/D"] + 0.02 * df["KPM"] + 0.006 * df["APM"] + 0.0058 * df["ADR"]
        df["Rating"] = df["Rating"].round(2)
        # Set to 0 where matches are 0
        df.loc[df["Matches"] == 0, ["KPM", "DPM", "APM", "ADR"]] = 0.0
        
        if "KPR" not in df.columns:
            df["KPR"] = 0.0
        if "DPR" not in df.columns:
            df["DPR"] = 0.0
        if "APR" not in df.columns:
            df["APR"] = 0.0
        if "MatchHistory" not in df.columns:
            df["MatchHistory"] = ""
        
        df = df.fillna(0)
        df["ELO"] = df["ELO"].round().astype(int)
        df = df.sort_values('ELO', ascending=False)
        global_context["database"] = df
        
        return jsonify({
            "success": True,
            "message": "Database reset successfully. All stats set to 0, ELO to 1000, and match history cleared."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def calculate_streak(player_name):
    """Calculate current win/lose streak for a player"""
    df_current = global_context["database"]
    player_data = df_current[df_current["Name"] == player_name]
    
    if player_data.empty:
        return {"type": "none", "count": 0}
    
    match_history_str = str(player_data.iloc[0].get("MatchHistory", ""))
    if not match_history_str or not match_history_str.strip():
        return {"type": "none", "count": 0}
    
    match_ids = [m.strip() for m in match_history_str.split(",") if m.strip()]
    if not match_ids:
        return {"type": "none", "count": 0}
    
    # Get matches in reverse order (newest first)
    match_ids.reverse()
    
    # Check the most recent matches to determine streak
    streak_type = None
    streak_count = 0
    
    for match_id in match_ids:
        match_path = f'./match_history/S4/{match_id}'
        if not os.path.exists(match_path):
            continue
        
        # Load match metadata
        metadata_path = f'{match_path}/metadata.json'
        winning_team = None
        if os.path.exists(metadata_path):
            try:
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    winning_team = metadata.get("winning_team", "Team 1")
            except:
                continue
        
        # Check which team the player was on
        t1_path = f'{match_path}/t1.csv'
        t2_path = f'{match_path}/t2.csv'
        
        player_team = None
        if os.path.exists(t1_path):
            try:
                t1_df = pd.read_csv(t1_path)
                if player_name in t1_df["Name"].values:
                    player_team = "Team 1"
            except:
                pass
        
        if player_team is None and os.path.exists(t2_path):
            try:
                t2_df = pd.read_csv(t2_path)
                if player_name in t2_df["Name"].values:
                    player_team = "Team 2"
            except:
                pass
        
        if player_team is None:
            continue
        
        # Determine if player won
        won = (winning_team == player_team)
        
        # Initialize streak type on first match
        if streak_type is None:
            streak_type = "win" if won else "loss"
            streak_count = 1
        elif (streak_type == "win" and won) or (streak_type == "loss" and not won):
            # Continue streak
            streak_count += 1
        else:
            # Streak broken
            break
    
    if streak_type is None:
        return {"type": "none", "count": 0}
    
    return {"type": streak_type, "count": streak_count}

@app.route('/api/database')
def get_database():
    """Get all players from database"""
    df_current = global_context["database"]
    
    # Get current online players
    online_df = get_random_players(df_current)
    online_players_set = set(online_df["Name"].tolist())
    
    players = []
    for _, row in df_current.iterrows():
        rank = get_rank(row["ELO"])
        icon_data = get_rank_icon_base64(rank)
        streak = calculate_streak(row["Name"])
        players.append({
            "name": row["Name"],
            "elo": int(row["ELO"]),
            "rating": round(row["Rating"], 2),
            "matches": int(row["Matches"]),
            "wins": int(row["Wins"]),
            "losses": int(row["Losses"]),
            "kd": round(row["K/D"], 2),
            "kpm": round(row["KPM"], 2),
            "dpm": round(row["DPM"], 2),
            "apm": round(row["APM"], 2),
            "adr": round(row["ADR"], 2),
            "rank": rank,
            "rank_icon": icon_data,
            "streak_type": streak["type"],
            "streak_count": streak["count"],
            "is_online": row["Name"] in online_players_set
        })
    return jsonify(players)

@app.route('/api/create-match', methods=['POST'])
def create_match():
    """Create a new match with random teams"""
    data = request.json
    online_list = data.get('online_players', [])
    
    if len(online_list) < 10:
        return jsonify({"error": "Not enough online players"}), 400
    
    team_1_names = sample(online_list, 5)
    team_2_names = sample([p for p in online_list if p not in team_1_names], 5)
    
    df_current = global_context["database"]
    df_1 = df_current.loc[df_current['Name'].isin(team_1_names)]
    df_2 = df_current.loc[df_current['Name'].isin(team_2_names)]
    
    ELO_1 = df_1["ELO"].sum()
    ELO_2 = df_2["ELO"].sum()
    
    map_name = np.random.choice(['Dust2', 'Inferno', 'Mirage', 'Vertigo', 'Anubis', 'Ancient', 'Train', 'Nuke'])
    elo_diff = ELO_1 - ELO_2
    t1_gain = 25 - min(25, (ELO_1 - ELO_2) // 50)
    t2_gain = 25 + min(25, (ELO_1 - ELO_2) // 50)
    
    # Format teams
    team_1 = []
    for _, row in df_1.iterrows():
        rank = get_rank(row["ELO"])
        icon_data = get_rank_icon_base64(rank)
        team_1.append({
            "name": row["Name"],
            "rank_icon": icon_data,
            "kd": round(row["K/D"], 2),
            "elo": int(row["ELO"])
        })
    
    team_2 = []
    for _, row in df_2.iterrows():
        rank = get_rank(row["ELO"])
        icon_data = get_rank_icon_base64(rank)
        team_2.append({
            "name": row["Name"],
            "rank_icon": icon_data,
            "kd": round(row["K/D"], 2),
            "elo": int(row["ELO"])
        })
    
    # Generate command
    command = "bot_kick\n"
    for i in range(5):
        command += f'bot_add_ct 3 "{team_1_names[i]}"\n'
        command += f'bot_add_t 3 "{team_2_names[i]}"\n'
    
    return jsonify({
        "team_1": team_1,
        "team_2": team_2,
        "map": map_name,
        "elo_diff": int(elo_diff),
        "t1_gain": int(t1_gain),
        "t2_gain": int(t2_gain),
        "command": command
    })

@app.route('/api/submit-match', methods=['POST'])
def submit_match():
    """Submit match results and update database"""
    data = request.json
    result_1 = pd.DataFrame(data['team_1_result'])
    result_2 = pd.DataFrame(data['team_2_result'])
    t1_gain = data['t1_gain']
    t2_gain = data['t2_gain']
    win_team = data['win_team']
    team1_score = int(data.get('team1_score', 16))
    team2_score = int(data.get('team2_score', 14))
    map_name = data.get('map', 'Unknown')  # Get map from request
    
    # Calculate total rounds (CS:GO matches go to 16 or overtime)
    total_rounds = team1_score + team2_score
    
    df_current = global_context["database"]
    players_1 = result_1["Name"].tolist()
    players_2 = result_2["Name"].tolist()
    average_elo = (df_current.loc[df_current["Name"].isin(players_1)]["ELO"].sum() + 
                   df_current.loc[df_current["Name"].isin(players_2)]["ELO"].sum()) // 10
    
    # Determine which team won and which ELO gain to use
    if win_team == "Team 1":
        winning_players = players_1
        winning_result = result_1
        losing_players = players_2
        losing_result = result_2
        elo_gain = t1_gain
    else:  # Team 2 wins
        winning_players = players_2
        winning_result = result_2
        losing_players = players_1
        losing_result = result_1
        elo_gain = t2_gain
    
    # Save match history first to get the path
    os.makedirs('./match_history/S4', exist_ok=True)
    match_dirs = [d for d in os.listdir('./match_history/S4') if os.path.isdir(f'./match_history/S4/{d}')]
    match_num = len(match_dirs) + 1
    match_path = f'./match_history/S4/match_{match_num}'
    os.makedirs(match_path, exist_ok=True)
    result_1.to_csv(f'{match_path}/t1.csv', index=False)
    result_2.to_csv(f'{match_path}/t2.csv', index=False)
    
    # Save match metadata (winning team, scores, map)
    match_metadata = {
        "winning_team": win_team,
        "team1_score": team1_score,
        "team2_score": team2_score,
        "match_num": match_num,
        "map": map_name
    }
    import json
    with open(f'{match_path}/metadata.json', 'w') as f:
        json.dump(match_metadata, f)
    
    # Store match in database
    db.create_match_record(
        match_num=match_num,
        team1_players=players_1,
        team2_players=players_2,
        team1_score=team1_score,
        team2_score=team2_score,
        winning_team=win_team,
        map_name=map_name,
        total_rounds=total_rounds
    )
    
    # Update map statistics
    db.update_map_stats(map_name, total_rounds, match_num)
    
    # Store match path for each player
    match_history_path = f'match_{match_num}'
    
    # Update winning team
    for player in winning_players:
        k = int(winning_result.loc[winning_result["Name"] == player]["K"])
        d = int(winning_result.loc[winning_result["Name"] == player]["D"])
        a = int(winning_result.loc[winning_result["Name"] == player]["A"])
        adr = int(winning_result.loc[winning_result["Name"] == player]["ADR"])
        mvp = int(winning_result.loc[winning_result["Name"] == player]["MVP"])
        
        # Calculate per-round stats
        kpr = round(k / total_rounds, 3) if total_rounds > 0 else 0.0
        dpr = round(d / total_rounds, 3) if total_rounds > 0 else 0.0
        apr = round(a / total_rounds, 3) if total_rounds > 0 else 0.0
        
        # Update cumulative stats
        df_current.loc[df_current["Name"] == player, 'Matches'] += 1
        df_current.loc[df_current["Name"] == player, "Wins"] += 1
        df_current.loc[df_current["Name"] == player, "TKills"] += k
        df_current.loc[df_current["Name"] == player, "TDeaths"] += d
        df_current.loc[df_current["Name"] == player, "TAssists"] += a
        df_current.loc[df_current["Name"] == player, "TADR"] += adr
        df_current.loc[df_current["Name"] == player, "MVP"] += mvp
        
        # Update per-round averages (weighted average)
        current_matches = df_current.loc[df_current["Name"] == player, "Matches"].values[0]
        if current_matches > 1:
            # Weighted average: (old_avg * (matches-1) + new_value) / matches
            old_kpr = df_current.loc[df_current["Name"] == player, "KPR"].values[0] if "KPR" in df_current.columns else 0.0
            old_dpr = df_current.loc[df_current["Name"] == player, "DPR"].values[0] if "DPR" in df_current.columns else 0.0
            old_apr = df_current.loc[df_current["Name"] == player, "APR"].values[0] if "APR" in df_current.columns else 0.0
            
            new_kpr = round((old_kpr * (current_matches - 1) + kpr) / current_matches, 3)
            new_dpr = round((old_dpr * (current_matches - 1) + dpr) / current_matches, 3)
            new_apr = round((old_apr * (current_matches - 1) + apr) / current_matches, 3)
        else:
            new_kpr = kpr
            new_dpr = dpr
            new_apr = apr
        
        df_current.loc[df_current["Name"] == player, "KPR"] = new_kpr
        df_current.loc[df_current["Name"] == player, "DPR"] = new_dpr
        df_current.loc[df_current["Name"] == player, "APR"] = new_apr
        
        # Update match history (append to existing)
        current_history = str(df_current.loc[df_current["Name"] == player, "MatchHistory"].values[0]) if "MatchHistory" in df_current.columns else ""
        if current_history:
            new_history = current_history + "," + match_history_path
        else:
            new_history = match_history_path
        df_current.loc[df_current["Name"] == player, "MatchHistory"] = new_history
        
        rating = get_rating(
            k / (d + 0.001),
            k,
            a,
            d,
            adr
        )
        
        elo_change = int(int(elo_gain) + min(15, int(rating * 5)) - 
                        int((df_current.loc[df_current["Name"] == player, "ELO"] - average_elo) * 0.03) + 
                        mvp * 10)
        df_current.loc[df_current["Name"] == player, "ELO"] += elo_change
    
    # Update losing team
    for player in losing_players:
        k = int(losing_result.loc[losing_result["Name"] == player]["K"])
        d = int(losing_result.loc[losing_result["Name"] == player]["D"])
        a = int(losing_result.loc[losing_result["Name"] == player]["A"])
        adr = int(losing_result.loc[losing_result["Name"] == player]["ADR"])
        
        # Calculate per-round stats
        kpr = round(k / total_rounds, 3) if total_rounds > 0 else 0.0
        dpr = round(d / total_rounds, 3) if total_rounds > 0 else 0.0
        apr = round(a / total_rounds, 3) if total_rounds > 0 else 0.0
        
        # Update cumulative stats
        df_current.loc[df_current["Name"] == player, "Matches"] += 1
        df_current.loc[df_current["Name"] == player, "Losses"] += 1
        df_current.loc[df_current["Name"] == player, "TKills"] += k
        df_current.loc[df_current["Name"] == player, "TDeaths"] += d
        df_current.loc[df_current["Name"] == player, "TAssists"] += a
        df_current.loc[df_current["Name"] == player, "TADR"] += adr
        
        # Update per-round averages (weighted average)
        current_matches = df_current.loc[df_current["Name"] == player, "Matches"].values[0]
        if current_matches > 1:
            # Weighted average: (old_avg * (matches-1) + new_value) / matches
            old_kpr = df_current.loc[df_current["Name"] == player, "KPR"].values[0] if "KPR" in df_current.columns else 0.0
            old_dpr = df_current.loc[df_current["Name"] == player, "DPR"].values[0] if "DPR" in df_current.columns else 0.0
            old_apr = df_current.loc[df_current["Name"] == player, "APR"].values[0] if "APR" in df_current.columns else 0.0
            
            new_kpr = round((old_kpr * (current_matches - 1) + kpr) / current_matches, 3)
            new_dpr = round((old_dpr * (current_matches - 1) + dpr) / current_matches, 3)
            new_apr = round((old_apr * (current_matches - 1) + apr) / current_matches, 3)
        else:
            new_kpr = kpr
            new_dpr = dpr
            new_apr = apr
        
        df_current.loc[df_current["Name"] == player, "KPR"] = new_kpr
        df_current.loc[df_current["Name"] == player, "DPR"] = new_dpr
        df_current.loc[df_current["Name"] == player, "APR"] = new_apr
        
        # Update match history (append to existing)
        current_history = str(df_current.loc[df_current["Name"] == player, "MatchHistory"].values[0]) if "MatchHistory" in df_current.columns else ""
        if current_history:
            new_history = current_history + "," + match_history_path
        else:
            new_history = match_history_path
        df_current.loc[df_current["Name"] == player, "MatchHistory"] = new_history
        
        rating = get_rating(
            k / (d + 0.001),
            k,
            a,
            d,
            adr
        )
        
        # For losing team, use the opposite team's gain value for loss calculation
        losing_elo_gain = t2_gain if win_team == "Team 1" else t1_gain
        elo_change = int(losing_elo_gain) + max(0, (10 - int(rating * 10))) + int((df_current.loc[df_current["Name"] == player, "ELO"] - average_elo) * 0.03)
        df_current.loc[df_current["Name"] == player, "ELO"] -= elo_change
    
    global_context["database"] = df_current
    db.bulk_update_from_dataframe(df_current)
    update_database_stats()
    
    # Get updated top 3 with rank icons
    df_updated = global_context["database"]
    top_3 = df_updated.head(3)
    top_3_list = []
    for _, row in top_3.iterrows():
        rank = get_rank(row["ELO"])
        icon_data = get_rank_icon_base64(rank)
        top_3_list.append({
            "Name": row["Name"],
            "ELO": int(row["ELO"]),
            "rank_icon": icon_data
        })
    
    return jsonify({
        "success": True,
        "top_3": top_3_list
    })

@app.route('/api/update-online-players', methods=['GET'])
def update_online_players():
    """Update online players list and top 3 - called automatically every hour"""
    df_updated = update_database_stats()
    online_df = get_random_players(df_updated)
    top_3 = df_updated.head(3)
    
    # Add rank icons to top 3
    top_3_list = []
    for _, row in top_3.iterrows():
        rank = get_rank(row["ELO"])
        icon_data = get_rank_icon_base64(rank)
        top_3_list.append({
            "Name": row["Name"],
            "ELO": int(row["ELO"]),
            "rank_icon": icon_data
        })
    
    return jsonify({
        "success": True,
        "top_3": top_3_list,
        "online_players": online_df["Name"].tolist()
    })

@app.route('/api/player-stats/<player_name>')
def get_player_stats(player_name):
    """Get detailed stats for a specific player"""
    df_current = global_context["database"]
    
    # Find player
    player_data = df_current[df_current["Name"] == player_name]
    
    if player_data.empty:
        return jsonify({"error": "Player not found"}), 404
    
    player = player_data.iloc[0]
    
    # Get match history
    match_history_str = str(player.get("MatchHistory", ""))
    match_history_list = []
    
    if match_history_str and match_history_str.strip():
        match_ids = [m.strip() for m in match_history_str.split(",") if m.strip()]
        
        for match_id in match_ids:
            match_path = f'./match_history/S4/{match_id}'
            if os.path.exists(match_path):
                try:
                    # Try to read both team files
                    t1_path = f'{match_path}/t1.csv'
                    t2_path = f'{match_path}/t2.csv'
                    
                    match_info = {"match_id": match_id, "player_stats": None}
                    
                    # Load match metadata to determine winning team and map
                    metadata_path = f'{match_path}/metadata.json'
                    winning_team = None
                    map_name = None
                    if os.path.exists(metadata_path):
                        try:
                            import json
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                                winning_team = metadata.get("winning_team", "Team 1")
                                map_name = metadata.get("map", None)
                        except:
                            winning_team = "Team 1"  # Default fallback
                    else:
                        winning_team = "Team 1"  # Default for old matches
                    
                    player_in_team1 = False
                    player_in_team2 = False
                    
                    # Check team 1
                    if os.path.exists(t1_path):
                        t1_df = pd.read_csv(t1_path)
                        player_row = t1_df[t1_df["Name"] == player_name]
                        if not player_row.empty:
                            player_in_team1 = True
                            match_info["player_stats"] = {
                                "k": int(player_row.iloc[0]["K"]),
                                "d": int(player_row.iloc[0]["D"]),
                                "a": int(player_row.iloc[0]["A"]),
                                "adr": float(player_row.iloc[0]["ADR"]),
                                "mvp": int(player_row.iloc[0]["MVP"]),
                                "team": "Team 1",
                                "won": (winning_team == "Team 1")
                            }
                    
                    # Check team 2
                    if not player_in_team1 and os.path.exists(t2_path):
                        t2_df = pd.read_csv(t2_path)
                        player_row = t2_df[t2_df["Name"] == player_name]
                        if not player_row.empty:
                            player_in_team2 = True
                            match_info["player_stats"] = {
                                "k": int(player_row.iloc[0]["K"]),
                                "d": int(player_row.iloc[0]["D"]),
                                "a": int(player_row.iloc[0]["A"]),
                                "adr": float(player_row.iloc[0]["ADR"]),
                                "mvp": int(player_row.iloc[0]["MVP"]),
                                "team": "Team 2",
                                "won": (winning_team == "Team 2")
                            }
                    
                    if match_info["player_stats"]:
                        match_info["map"] = map_name  # Add map to match info
                        match_history_list.append(match_info)
                except Exception as e:
                    print(f"Error reading match {match_id}: {e}")
                    continue
    
    # Get rank icon
    rank = get_rank(player["ELO"])
    rank_icon = get_rank_icon_base64(rank)
    
    # Prepare player stats
    stats = {
        "name": player["Name"],
        "elo": int(player["ELO"]),
        "rank": rank,
        "rank_icon": rank_icon,
        "matches": int(player["Matches"]),
        "wins": int(player["Wins"]),
        "losses": int(player["Losses"]),
        "win_rate": round((player["Wins"] / player["Matches"] * 100) if player["Matches"] > 0 else 0, 1),
        "kd": round(player["K/D"], 2),
        "kpr": round(player.get("KPR", 0.0), 3),
        "dpr": round(player.get("DPR", 0.0), 3),
        "apr": round(player.get("APR", 0.0), 3),
        "kpm": round(player["KPM"], 2),
        "dpm": round(player["DPM"], 2),
        "apm": round(player["APM"], 2),
        "adr": round(player["ADR"], 2),
        "rating": round(player["Rating"], 2),
        "total_kills": int(player["TKills"]),
        "total_deaths": int(player["TDeaths"]),
        "total_assists": int(player["TAssists"]),
        "mvp_count": int(player["MVP"]),
        "match_history": match_history_list
    }
    
    return jsonify(stats)

def preprocess_image(image_bytes):
    """Preprocess image for better OCR accuracy"""
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
    
    # Threshold to get better text contrast
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def parse_csgo_stats(text_lines, all_player_names):
    """Parse OCR text to extract player statistics from CS:GO match stats"""
    players = []
    
    # Multiple patterns to handle different formats
    # Pattern 1: K D A ADR MVP (5 numbers in sequence)
    stats_pattern1 = re.compile(r'(\d+)[\s|]+(\d+)[\s|]+(\d+)[\s|]+(\d+\.?\d*)[\s|]+(\d+)')
    # Pattern 2: More flexible - allows for variations
    stats_pattern2 = re.compile(r'(\d+)[\s|,]+(\d+)[\s|,]+(\d+)[\s|,]+(\d+\.?\d*)[\s|,]*(\d*)')
    # Pattern 3: Just K D A ADR (MVP might be separate or missing)
    stats_pattern3 = re.compile(r'(\d+)[\s|]+(\d+)[\s|]+(\d+)[\s|]+(\d+\.?\d*)')
    
    # Combine all text for better matching
    full_text = ' '.join(text_lines)
    
    # Strategy 1: Find player names and extract nearby stats
    for player_name in all_player_names:
        # Try different name matching strategies
        name_variations = [
            player_name,
            player_name.replace(' ', ''),
            player_name.split()[-1] if ' ' in player_name else player_name,  # Last name only
        ]
        
        for name_variant in name_variations:
            # Find player name in text (case insensitive)
            name_pattern = re.escape(name_variant)
            name_match = re.search(name_pattern, full_text, re.IGNORECASE)
            
            if name_match:
                # Extract context around the player name (200 chars before and after)
                start = max(0, name_match.start() - 100)
                end = min(len(full_text), name_match.end() + 200)
                context = full_text[start:end]
                
                # Try to find stats near the player name
                stats_match = None
                
                # Try pattern 1 (K D A ADR MVP)
                stats_match = stats_pattern1.search(context)
                if stats_match:
                    k, d, a, adr, mvp = stats_match.groups()
                    players.append({
                        "name": player_name,
                        "k": int(k),
                        "d": int(d),
                        "a": int(a),
                        "adr": float(adr),
                        "mvp": int(mvp) if mvp else 0
                    })
                    break
                
                # Try pattern 2 (more flexible)
                stats_match = stats_pattern2.search(context)
                if stats_match:
                    k, d, a, adr, mvp = stats_match.groups()
                    if k and d and a and adr:
                        players.append({
                            "name": player_name,
                            "k": int(k),
                            "d": int(d),
                            "a": int(a),
                            "adr": float(adr),
                            "mvp": int(mvp) if mvp else 0
                        })
                        break
                
                # Try pattern 3 (K D A ADR only, MVP = 0)
                stats_match = stats_pattern3.search(context)
                if stats_match:
                    k, d, a, adr = stats_match.groups()
                    players.append({
                        "name": player_name,
                        "k": int(k),
                        "d": int(d),
                        "a": int(a),
                        "adr": float(adr),
                        "mvp": 0
                    })
                    break
    
    # Strategy 2: If we found some players but not all, try line-by-line parsing
    if len(players) < 5:
        for i, line in enumerate(text_lines):
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 5:
                continue
            
            # Check if line contains a player name
            for player_name in all_player_names:
                if player_name.lower() in line_clean.lower():
                    # Check if this player is already found
                    if any(p["name"] == player_name for p in players):
                        continue
                    
                    # Look for stats in current line and next 2 lines
                    search_text = line_clean
                    for j in range(1, 3):
                        if i + j < len(text_lines):
                            search_text += " " + text_lines[i + j].strip()
                    
                    # Try all patterns
                    for pattern in [stats_pattern1, stats_pattern2, stats_pattern3]:
                        match = pattern.search(search_text)
                        if match:
                            groups = match.groups()
                            if len(groups) >= 4:
                                k, d, a, adr = int(groups[0]), int(groups[1]), int(groups[2]), float(groups[3])
                                mvp = int(groups[4]) if len(groups) > 4 and groups[4] else 0
                                players.append({
                                    "name": player_name,
                                    "k": k,
                                    "d": d,
                                    "a": a,
                                    "adr": adr,
                                    "mvp": mvp
                                })
                                break
                    break
    
    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_players = []
    for p in players:
        if p["name"] not in seen:
            seen.add(p["name"])
            unique_players.append(p)
    
    return unique_players

def extract_stats_from_image(image_bytes):
    """Extract player stats from CSGO match screenshot using OCR"""
    if not init_ocr():
        return {"error": "OCR not available. Please install EasyOCR: pip install easyocr"}
    
    try:
        # Preprocess image
        processed_img = preprocess_image(image_bytes)
        
        # Use EasyOCR to extract text
        results = ocr_reader.readtext(processed_img)
        
        # Combine all detected text with confidence and position info
        all_text = []
        for (bbox, text, confidence) in results:
            if confidence > 0.2:  # Lower threshold to catch more text
                cleaned_text = text.strip()
                if cleaned_text and len(cleaned_text) > 0:
                    all_text.append(cleaned_text)
        
        # Get player names from database
        df_current = global_context["database"]
        all_player_names = df_current["Name"].tolist()
        
        # Parse extracted text to find player stats
        players_data = parse_csgo_stats(all_text, all_player_names)
        print(all_text)
        # Return more debugging info
        return {
            "success": len(players_data) > 0,
            "players": players_data,
            "raw_text": all_text[:30],  # Return first 30 lines for debugging
            "total_text_lines": len(all_text),
            "players_found": len(players_data),
            "message": f"Found {len(players_data)} players" if players_data else "No players found. Check raw_text for OCR output."
        }
    except Exception as e:
        import traceback
        return {"error": f"OCR processing failed: {str(e)}\n{traceback.format_exc()}"}

@app.route('/api/upload-screenshot', methods=['POST'])
def upload_screenshot():
    """Handle screenshot upload and extract stats"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Read image bytes
    image_bytes = file.read()
    
    # Extract stats
    result = extract_stats_from_image(image_bytes)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

