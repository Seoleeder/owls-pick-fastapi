#app\core\config.py

import os
from dotenv import load_dotenv
from app.core.logger import setup_logger

logger = setup_logger(__name__)

def init_config():
    """
    애플리케이션 초기 설정 함수
    .env 파일에서 환경 변수 로드
    """
    
    # .env 파일에서 환경변수 로드
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    # API 키가 없으면 서버 구동 X (런타임 에러 방지)
    if not api_key:
        logger.error("GEMINI_API_KEY is not set in the .env file.")
        raise ValueError("GEMINI_API_KEY is missing. Check your .env configuration.")
    
    logger.info("Google Gemini API configuration completed successfully.")