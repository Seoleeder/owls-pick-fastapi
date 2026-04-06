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
    
    # Vertex AI용 GCP 서비스 계정 인증 키 경로 로드
    gcp_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # GCP 인증 키가 없으면 서버 구동 중지 (런타임 에러 방지)
    if not gcp_credentials:
        logger.error("GOOGLE_APPLICATION_CREDENTIALS is not set in the .env file.")
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is missing. Check your .env configuration.")
    
    logger.info("Google Cloud Vertex AI configuration completed successfully.")