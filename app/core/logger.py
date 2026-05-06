#app\core\logger.py

import logging
import sys
import os
from dotenv import load_dotenv
from logging_loki import LokiHandler

# .env 파일에서 환경변수 로드
load_dotenv()

def setup_logger(name: str) -> logging.Logger:
    """
    모듈별 커스텀 로거 생성 및 설정 팩토리 함수.
    logger = setup_logger(__name__)
    """
    logger = logging.getLogger(name)
    
    # 로거 호출 시 핸들러 중복 추가 방지용 방어 로직
    if not logger.handlers:
        # 환경변수 기반 로그 레벨 할당 (기본값: INFO)
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # logging 라이브러리 상수 타입으로 변환
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        logger.setLevel(log_level)
        
        # 로컬 디버깅용 콘솔 출력 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # 로그 출력 포맷 지정
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        # 통합 로그 수집용 Loki 전송 핸들러 설정
        loki_url = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/push")
        
        loki_handler = LokiHandler(
            url=loki_url,
            # AI 엔진 식별용 Label 지정
            tags={"application": "owls-pick-fastapi"},
            version="1",
        )
        loki_handler.setLevel(log_level)
        
        logger.addHandler(loki_handler)
        
    return logger