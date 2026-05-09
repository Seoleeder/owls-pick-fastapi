#app\core\logger.py

import logging
import sys
import os
from dotenv import load_dotenv
from logging_loki import LokiHandler
from app.core.middleware import trace_id_var

# .env 파일에서 환경변수 로드
load_dotenv()

# LogRecord에 trace_id 속성을 동적으로 할당하는 커스텀 필터
class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = trace_id_var.get()
        return True

def setup_logger(name: str) -> logging.Logger:
    """
    모듈별 커스텀 로거 생성 및 설정 팩토리 함수.
    logger = setup_logger(__name__)
    """
    logger = logging.getLogger(name)
    
    # 로거 호출 시 핸들러 중복 추가 방지
    if not logger.handlers:
        # 환경변수 기반 로그 레벨 설정 (기본값: INFO)
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # logging 라이브러리 상수 타입으로 변환
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        logger.setLevel(log_level)
        
        # Trace ID 주입용 커스텀 필터 인스턴스 생성
        trace_filter = TraceIdFilter()
        
        # 로그 출력 포맷 지정 
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(trace_id)s] - %(name)s - %(message)s"
        )
        
        # 로컬 디버깅용 콘솔 출력 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.addFilter(trace_filter) # 콘솔 출력 전 Trace ID 필터 등록

        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        # 통합 모니터링용 Loki 전송 핸들러 설정
        loki_url = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/push")
        
        loki_handler = LokiHandler(
            url=loki_url,
            tags={"application": "owls-pick-fastapi"},  # AI 엔진 식별용 Label
            version="1",
        )
        loki_handler.setLevel(log_level)
        loki_handler.addFilter(trace_filter) # Loki 서버 전송 전 Trace ID 필터 등록
        loki_handler.setFormatter(formatter) # Trace ID가 포함된 포맷으로 전송 데이터 구성
        
        logger.addHandler(loki_handler)
        
    return logger