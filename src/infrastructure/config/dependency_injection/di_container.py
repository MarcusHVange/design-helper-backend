from fastapi import Depends
from src.infrastructure.config.app_config import AppConfig
from src.infrastructure.services.ai_search_service import AISearchService

def get_app_config() -> AppConfig:
    return AppConfig()

def get_ai_search_service(app_config: AppConfig = Depends(get_app_config)) -> AISearchService:
    return AISearchService(app_config)