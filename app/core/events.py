#app\core\events.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import init_config
from app.core.settings import get_settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 생명주기(시작/종료) 관리
    """
    logger.info("Starting up Owl's Pick AI Microservice...")
    
    # 환경변수 로드 및 OpenAI API 초기화
    init_config()
    
    # Pydantic Settings 객체 생성 및 메모리 캐싱
    get_settings()
    
    yield 
    
    logger.info("Shutting down AI Microservice. Cleaning up resources...")