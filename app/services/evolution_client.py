import httpx

from app.core.config import settings


class EvolutionClient:

    def __init__(self):
        self.base_url = settings.EVOLUTION_BASE_URL
        self.headers = {
            "apikey": settings.EVOLUTION_API_KEY
        }

    async def health(self):

        async with httpx.AsyncClient() as client:

            response = await client.get(
                self.base_url,
                headers=self.headers
            )

            return response.json()