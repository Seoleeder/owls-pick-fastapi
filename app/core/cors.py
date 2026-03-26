#app\core\cors.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI):
    """
    CORS 미들웨어 설정
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # 운영 시 실제 Spring Boot IP로 변경 필요
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )