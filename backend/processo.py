import os
import sys

os.environ['HADOOP_HOME'] = "C:\\hadoop"
sys.path.append("C:\\hadoop\\bin")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def processar():
    spark = SparkSession.builder \
        .appName("Processador_LoL") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()

    # Lendo o arquivo
    df = spark.read.json("data/data_partidas/match_data.jsonl")

    df_players = df.select(F.explode("info.participants").alias("p"))

    # 2. Pegamos os dados exatos
    df_limpo = df_players.select(
        F.col("p.championName").alias("campeao"),
        F.col("p.win").alias("venceu"),
        F.col("p.individualPosition").alias("rota"),
        F.col("p.kills").alias("kills"),
        F.col("p.deaths").alias("deaths"),
        F.col("p.assists").alias("assists")
    )

    # 3. Criamos o resumo (Ranking)
    # Isso transforma milhões de linhas em uma tabela pequena de performance
    ranking = df_limpo.groupBy("campeao", "rota") \
        .agg(
            F.avg(F.when(F.col("venceu") == True, 1).otherwise(0)).alias("win_rate"),
            F.count("campeao").alias("popularidade")
        ).filter(F.col("popularidade") > 100)

    ranking.write.mode("overwrite").parquet("data/meta_high_elo.parquet")
    

if __name__ == "__main__":
    processar()
