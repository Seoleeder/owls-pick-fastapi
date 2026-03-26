#app\core\logger.py

import logging
import sys
import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

def setup_logger(name: str) -> logging.Logger:
    """
    모듈별 커스텀 로거 생성 및 설정 팩토리 함수.
    logger = setup_logger(__name__)
    """
    logger = logging.getLogger(name)
    
    # 핸들러 중복 추가 방지 (여러 번 호출되어 로그가 여러번 출력되는 현상 방지)
    if not logger.handlers:
        # .env에서 LOG_LEVEL을 가져오고, 없으면 'INFO' 
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # 실제 logging 라이브러리 상수로 변환
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        logger.setLevel(log_level)
        
        # 콘솔 출력 핸들러 설정
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        # 로그 포맷 지정
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
    return logger