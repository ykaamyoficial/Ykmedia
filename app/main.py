from fastapi import FastAPI

from app.services.evolution_client import EvolutionClient

app = FastAPI()

evolution = EvolutionClient()


@app.get("/")
async def home():

    return {
        "project": "YkMedia"
    }


@app.get("/evolution")
async def evolution_status():

    return await evolution.health()