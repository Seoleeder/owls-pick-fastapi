#main.py

from fastapi import FastAPI

# 설정 및 로거
from app.core.logger import setup_logger

from app.core.events import lifespan
from app.core.cors import setup_cors

# API 라우터 
from app.api import localization

logger = setup_logger("main")

# FastAPI 애플리케이션 객체 생성
app = FastAPI(
    title="Owl's Pick AI Microservice",
    description="게임 데이터 번역, OWLS 챗봇 등 AI 기반 마이크로서비스 API",
    version="1.0.0",
    lifespan=lifespan
)

# 미들웨어(CORS) 적용
setup_cors(app)

# API 라우터 등록 
app.include_router(
    localization.router, 
    prefix="/api/localization", 
    tags=["Game Localization"]
)

# app.include_router(chat.router, prefix="/api/v1/chat", tags=["2. AI Chatbot"])


# 5. Health Check 엔드포인트
@app.get("/health", tags=["System"])
async def health_check():
    """MSA 환경(Docker, k8s 등)에서 서버가 살아있는지 확인하는 용도"""
    return {"status": "ok", "service": "owls-pick-ai"}