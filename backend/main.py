from fastapi import FastAPI
from recomenda import recomenda_campeoes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Recomendador de Campeões de League of Legends"}

@app.get("/recomenda/{jogador}")
def recomenda(jogador: str):
    return recomenda_campeoes(jogador)