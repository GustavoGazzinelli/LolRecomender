import json
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.linalg import Vectors
from riotApi import *

def padroniza(coluna):
    return F.regexp_replace(F.lower(F.col(coluna)), r"[^a-z0-0]", "")

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
    nome, tag = separar_riot_id(riot_id)

    # 1. Coleta partidas usuário
    data = collect_player_matches(nome, tag)
    save_matches_csv(data)

    spark = get_spark()

    # 2. Carregar dados
    df_partidas = spark.read.csv(
        "data/partidas.csv",
        header=True,
        inferSchema=True,
        sep=";"
    )

    df_champs = spark.read.csv("data/champions.csv", header=True, inferSchema=True, sep=";") \
    .withColumn("join_id", padroniza("champion"))

    df_meta = spark.read.parquet("data/meta_high_elo.parquet") \
    .withColumn("join_id", padroniza("campeao"))

    # join dados player + champions
    df_player = df_partidas.join(
        df_champs,
        df_partidas["campeao"] == df_champs["champion"],
        "left"
    )

    # 3. Campeões já jogados
    ja_jogados = [
        row["campeao"]
        for row in df_partidas.select("campeao").distinct().collect()
    ]

    # 4. Rotas favoritas
    rotas = (
        df_partidas.groupBy("rota")
        .count()
        .orderBy(F.col("count").desc())
        .limit(2)
        .collect()
    )

    rotas_fav = [row["rota"] for row in rotas]

    # 5. Perfil médio do usuário
    feature_cols = ["attack", "defense", "magic", "difficulty"]
    performance_cols = ["kills", "assists", "vision"]

    colunas_para_media = feature_cols + performance_cols
    user_profile_row = df_player.agg(
        *[F.avg(col).alias(col) for col in colunas_para_media]
    ).first()

    user_profile = user_profile_row.asDict()

    dificuldade_media = user_profile["difficulty"]

    # 6. Filtrar meta pela rota
    candidatos = (
        df_meta.filter(F.col("rota").isin(rotas_fav))
        .filter(~F.col("campeao").isin(ja_jogados))
    )

    # junta meta + stats champions
    candidatos = candidatos.join(
        df_champs,
        candidatos["campeao"] == df_champs["champion"],
        "left"
    )

    # 7. Similaridade do player
    distancia = None

    for col in feature_cols:
        termo = F.pow(F.col(col) - float(user_profile[col]), 2)

        if distancia is None:
            distancia = termo
        else:
            distancia += termo

    candidatos = candidatos.withColumn(
        "dist",
        F.sqrt(distancia)
    )

    # 8. Score híbrido
    candidatos = candidatos.withColumn(
        "similaridade_score",
        1 / (1 + F.col("dist"))
    )

    candidatos = candidatos.withColumn(
        "popularidade_score",
        F.log1p(F.col("popularidade"))
    )

    candidatos = candidatos.withColumn(
        "dificuldade_score",
        (10 - F.abs(F.col("difficulty") - dificuldade_media)) / 10
    )

    candidatos = candidatos.withColumn(
        "score_final",
        (F.col("similaridade_score") * 0.4) +
        (F.col("win_rate") * 0.4) +
        (F.col("popularidade_score") * 0.1) +
        (F.col("dificuldade_score") * 0.1)
    )

    recomendacoes_df = (
        candidatos.orderBy(F.col("score_final").desc())
        .limit(3)
    )

    # 9. Formatar resposta
    lista_recomendacoes = []

    for row in recomendacoes_df.collect():
        champ = row["campeao"]

        lista_recomendacoes.append({
            "nome": champ,
            "win_rate": round(row["win_rate"], 3),
            "popularidade": row["popularidade"],
            "score": round(row["score_final"], 4),
            "tags": row["tags"],
            "dificuldade": row["difficulty"],
            "icon": CHAMPION_ASSETS.get(champ, {}).get("icon"),
            "splash": CHAMPION_ASSETS.get(champ, {}).get("splash"),
        })

    return {
        "invocador": nome,
        "tag_nome": tag,
        "rotas_favoritas": rotas_fav,
        "perfil_medio": {
            "attack": round(user_profile["attack"], 2),
            "defense": round(user_profile["defense"], 2),
            "magic": round(user_profile["magic"], 2),
            "difficulty": round(user_profile["difficulty"], 2),
            "media_kills": round(user_profile.get("kills", 0), 1),
            "media_assists": round(user_profile.get("assists", 0), 1),
            "media_visao": round(user_profile.get("vision", 0), 1)
        },
        "recomendacoes": lista_recomendacoes
    }