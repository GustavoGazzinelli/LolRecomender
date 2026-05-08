import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}

def get_puuid(nome, tag):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{nome}/{tag}"

    response = requests.get(url, headers=HEADERS)
    return response.json()["puuid"]

def get_match_ids(puuid, count=50):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"

    response = requests.get(url, headers=HEADERS)
    return response.json()

def get_match_details(match_id):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"

    response = requests.get(url, headers=HEADERS)
    return response.json()

def extract_player_data(match_data, puuid):
    for p in match_data["info"]["participants"]:
        if p["puuid"] == puuid:
            return {
                "invocador": p["riotIdGameName"],
                "campeao": p["championName"],
                "rota": p["teamPosition"],
                "win": int(p["win"]),

                "kills": p["kills"],
                "deaths": p["deaths"],
                "assists": p["assists"],

                "kda": round((p["kills"] + p["assists"]) / max(p["deaths"], 1), 2),

                "dano_campeao": p["totalDamageDealtToChampions"],
                "dano_tomado": p["totalDamageTaken"],
                "ouro": p["goldEarned"],
                "vision": p["visionScore"]
            }
            
def collect_player_matches(nome, tag):
    puuid = get_puuid(nome, tag)
    match_ids = get_match_ids(puuid)

    data = []

    for match_id in match_ids:
        try:
            match = get_match_details(match_id)
            player_data = extract_player_data(match, puuid)

            if player_data:
                data.append(player_data)

        except Exception as e:
            print(f"Erro match {match_id}: {e}")

    return data

import pandas as pd

def save_matches_csv(data):
    df = pd.DataFrame(data)

    df.to_csv(
        "data/partidas.csv",
        index=False,
        sep=";"
    )