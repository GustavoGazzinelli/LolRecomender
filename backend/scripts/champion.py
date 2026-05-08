import requests
import json

VERSION = "15.10.1"

url = f"https://ddragon.leagueoflegends.com/cdn/{VERSION}/data/en_US/champion.json"

response = requests.get(url)
data = response.json()

champions = data["data"]
mapped = {}

for champ_key, champ in champions.items():
    champ_id = champ["id"]

    mapped[champ_id] = {
        "id": champ_id,
        "name": champ["name"],
        "splash": f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champ_id}_0.jpg",
        "icon": f"https://ddragon.leagueoflegends.com/cdn/{VERSION}/img/champion/{champ_id}.png"
    }

with open("champions_data.json", "w", encoding="utf-8") as file:
    json.dump(mapped, file, indent=4, ensure_ascii=False)

print("Arquivo champions_data.json criado com sucesso!")