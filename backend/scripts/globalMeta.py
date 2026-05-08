import requests
import pandas as pd
import os

def build_dataset():
    print("Baixando Data Dragon...")

    # Cria a pasta data se não existir
    if not os.path.exists('data'):
        os.makedirs('data')

    version = requests.get(
        "https://ddragon.leagueoflegends.com/api/versions.json"
    ).json()[0]

    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    data = requests.get(url).json()["data"]

    # Mapeamento manual das rotas (Lanes) mais comuns
    # Como a API não dá isso, precisamos definir para o filtro do Spark funcionar
    lanes_map = {
        "Top": ["Aatrox", "Camille", "Darius", "Fiora", "Garen", "Gnar", "Gwen", "Illaoi", "Irelia", "Jax", "Jayce", "K'Sante", "Kayle", "Kennen", "Kled", "Malphite", "Mordekaiser", "Nasus", "Olaf", "Ornn", "Pantheon", "Poppy", "Quinn", "Renekton", "Riven", "Rumble", "Sett", "Shen", "Singed", "Sion", "Teemo", "Tryndamere", "Urgot", "Vayne", "Volibear", "Yorick"],
        "Jungle": ["Amumu", "Bel'Veth", "Briar", "Diana", "Ekko", "Elise", "Evelynn", "Fiddlesticks", "Graves", "Hecarim", "Ivern", "Jarvan IV", "Karthus", "Kayn", "Kha'Zix", "Kindred", "Lee Sin", "Lillia", "Master Yi", "Nidalee", "Nocturne", "Nunu & Willump", "Rammus", "Rek'Sai", "Rengar", "Sejuani", "Shaco", "Shyvana", "Skarner", "Taliyah", "Trundle", "Udyr", "Vi", "Viego", "Warwick", "Xin Zhao", "Zac"],
        "Mid": ["Ahri", "Akali", "Akshan", "Anivia", "Annie", "Aurelion Sol", "Azir", "Cassiopeia", "Corki", "Fizz", "Galio", "Hwei", "Kassadin", "Katarina", "LeBlanc", "Lissandra", "Lux", "Malzahar", "Naafiri", "Neeko", "Orianna", "Ryze", "Sylas", "Syndra", "Talon", "Twisted Fate", "Veigar", "Vel'Koz", "Viktor", "Vladimir", "Xerath", "Yasuo", "Yone", "Zoe", "Zed"],
        "Bottom": ["Aphelios", "Ashe", "Caitlyn", "Draven", "Ezreal", "Jhin", "Jinx", "Kai'Sa", "Kalista", "Kog'Maw", "Lucian", "Miss Fortune", "Nilah", "Samira", "Sivir", "Tristana", "Twitch", "Varus", "Vayne", "Xayah", "Zeri"],
        "Utility": ["Alistar", "Bard", "Blitzcrank", "Brand", "Braum", "Janna", "Karma", "Leona", "Lulu", "Milio", "Morgana", "Nami", "Nautilus", "Pyke", "Rakan", "Rell", "Renata Glasc", "Senna", "Seraphine", "Sona", "Soraka", "Tahm Kench", "Taric", "Thresh", "Yuumi", "Zilio", "Zyra"]
    }

    rows = []

    for champ_id, champ in data.items():
        name = champ["name"]
        
        lane_encontrada = "Outros"
        for lane, champs in lanes_map.items():
            if name in champs:
                lane_encontrada = lane
                break

        rows.append({
            "champion": name,
            "lane": lane_encontrada,
            "tags": ",".join(champ["tags"]),
            "difficulty": champ["info"]["difficulty"],
            "attack": champ["info"]["attack"],
            "defense": champ["info"]["defense"],
            "magic": champ["info"]["magic"]
        })

    df = pd.DataFrame(rows)
    
    df.to_csv("data/champions.csv", sep=";", index=False, encoding="utf-8")

    print(f"CSV gerado! Total de campeões: {len(df)}")
    print(f"Campeões como 'Outros': {len(df[df['lane'] == 'Outros'])}")

if __name__ == "__main__":
    build_dataset()