from fastapi import FastAPI, Depends
from src.core.services.abs_ai_search_service import AbsAISearchService
from src.infrastructure.config.dependency_injection.di_container import get_ai_search_service

app = FastAPI(
    title="Design Helper API",
    description="API for Design Helper application",
    version="0.1.0"
)


@app.get("/")
async def root(
    ai_search_service: AbsAISearchService = Depends(get_ai_search_service)
):
    response = ai_search_service.search()
    return response