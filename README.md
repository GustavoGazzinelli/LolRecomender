# Projeto de Recomendação de Campeões - League of Legends

## Dataset

Ao baixar coloque os arquivos dentro da pasta "backend/data/data_partidas/"

https://www.kaggle.com/datasets/californianbill/patch-25-14-lol-league-of-legends-ranked-games?hl=pt-BR

## Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main::app --reload
```

## Frontend

Abra outro terminal

```bash
cd frontend
npm install
npm ci
npm run dev
```

## .env

Lembre-se de criar um .env com RIOT_API_KEY você pode conseguir essa chave acessando sua conta mesmo da riot nesse site

https://developer.riotgames.com/

## Cabou-se
