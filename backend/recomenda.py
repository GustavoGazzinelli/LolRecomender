import json
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.linalg import Vectors
from riotApi import *


def carregar_assets_campeoes():
    arquivo = Path(__file__).resolve().parent / "data" / "champions_data.json"
    with arquivo.open(encoding="utf-8") as f:
        dados = json.load(f)

    assets = {}
    for champ_id, meta in dados.items():
        assets[champ_id] = meta
        nome = meta.get("name")
        if nome:
            assets[nome] = meta

    return assets


CHAMPION_ASSETS = carregar_assets_campeoes()

def get_spark():
    return SparkSession.builder \
        .appName("LoLRecommender") \
        .master("local[*]") \
        .config("spark.sql.execution.pyspark.udf.faulthandler.enabled", "true") \
        .getOrCreate()

def separar_riot_id(riot_id):
    if "#" not in riot_id:
        raise ValueError("Formato inválido. Use Nome#TAG")
    nome, tag = riot_id.split("#")
    return nome, tag

def recomenda_campeoes(riot_id):
    # 1. Coleta de dados
    nome, tag = separar_riot_id(riot_id)
    data = collect_player_matches(nome, tag)
    save_matches_csv(data)

    spark = get_spark()
    
    # 2. Leitura dos arquivos
    df_partidas = spark.read.csv(
        "data/partidas.csv",
        header=True,
        inferSchema=True,
        sep=";"
    )
    
    df_champs = spark.read.csv(
        "data/champions.csv", 
        header=True, 
        inferSchema=True, 
        sep=";"
    )
    
    df_partidas_detalhado = df_partidas.join(
        df_champs, 
        df_partidas["campeao"] == df_champs["champion"], 
        "left"
    )
    
    # 3. Definição dos Perfis de Referência
    perfis_dados = [
        (10.0, 5.0, 12.0, 35000.0, 20000.0, "Agressivo"),
        (2.0, 18.0, 35.0, 10000.0, 15000.0, "Estrategista"),
        (4.0, 12.0, 15.0, 15000.0, 45000.0, "Linha de Frente"),
    ]
    colunas_stats = ["kills", "assists", "vision", "dano_campeao", "dano_tomado"]
    df_perfis = spark.createDataFrame(perfis_dados, colunas_stats + ["perfil_nome"])
    
    # 4. Cálculo das médias do usuário
    user_stats_row = df_partidas_detalhado.agg(
        F.avg("difficulty").alias("dif_media"),
        F.avg("kills").alias("kills"),
        F.avg("assists").alias("assists"),
        F.avg("vision").alias("vision"),
        F.avg("dano_campeao").alias("dano_campeao"),
        F.avg("dano_tomado").alias("dano_tomado")
    ).first()
    
    # Transformamos em dicionário para facilitar o acesso
    user_avg = user_stats_row.asDict()
    dif = user_avg["dif_media"]
    
    # Calculamos a distância euclidiana comparando as médias do user com os perfis fixos
    perfil_detectado = df_perfis.withColumn("dist", 
        F.sqrt(
            F.pow(F.col("kills") - user_avg["kills"] * 1000, 2) +
            F.pow(F.col("assists") - user_avg["assists"] * 500, 2) +
            F.pow(F.col("vision") - user_avg["vision"] * 500, 2) +
            F.pow(F.col("dano_campeao") - user_avg["dano_campeao"], 2) +
            F.pow(F.col("dano_tomado") - user_avg["dano_tomado"], 2)
        )
    ).orderBy("dist").select("perfil_nome").first()["perfil_nome"]

    # 6. Filtragem de Recomendações
    ja_jogados = [row['campeao'] for row in df_partidas.select("campeao").distinct().collect()]
    
    rotas = df_partidas.groupBy("rota") \
        .count() \
        .orderBy("count", ascending=False) \
        .limit(2) \
        .collect()
        
    rotas_fav = [row["rota"] for row in rotas]
    
    query_dificuldade = (F.col("difficulty") <= (dif + 4))
    
    if perfil_detectado == "Agressivo":
        query = (F.col("attack") >= 7) | (F.col("magic") >= 7)
    elif perfil_detectado == "Estrategista":
        query = F.col("tags").contains("Support")
    elif perfil_detectado == "Linha de Frente":
        query = F.col("defense") >= 7
    else:
        query = F.col("difficulty") <= 5

    recomendacoes_df = df_champs.filter(query) \
        .filter(query_dificuldade) \
        .filter(F.col("lane").isin(rotas_fav)) \
        .filter(~F.col("champion").isin(ja_jogados)) \
        .orderBy(F.rand()) \
        .limit(3)
        
    lista_recomendacoes = [
        {
            "nome": row["champion"],
            "tags": row["tags"],
            "dificuldade": row["difficulty"],
            "icon": CHAMPION_ASSETS.get(row["champion"], {}).get("icon"),
            "splash": CHAMPION_ASSETS.get(row["champion"], {}).get("splash"),
        } for row in recomendacoes_df.collect()
    ]
    
    # 7. Retorno formatado
    return {
        "invocador": nome,
        "tag_nome": tag,
        "perfil_identificado": perfil_detectado,
        "estatisticas_medias": {
            "kills": round(user_avg["kills"], 2),
            "assists": round(user_avg["assists"], 2),
            "vision": round(user_avg["vision"], 2)
        },
        "recomendacoes": lista_recomendacoes
    }