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
        
        # 분산 추적용 Trace ID 주입
        record.trace_id = trace_id_var.get()
        
        # LokiHandler가 매 로그마다 심각도(level)를 식별할 수 있도록 태그 병합
        if not hasattr(record, "tags") or record.tags is None:
            record.tags = {}
            
        record.tags.update({
            "application": "owls-pick-fastapi",
            "level": record.levelname
        })
        
        return True
    
def attach_global_loki_handler(loki_handler: LokiHandler, trace_filter: logging.Filter):
    """
    Uvicorn 및 FastAPI 전역 시스템 예외 발생 시 Loki 전송 핸들러 바인딩 함수.
    """
    # 치명적 시스템 예외 포착을 위한 타겟 로거 한정
    target_loggers = ["uvicorn.error", "fastapi"]

    for logger_name in target_loggers:
        sys_logger = logging.getLogger(logger_name)
        
        # 로거 호출 시 핸들러 및 필터 중복 추가 방지
        if not any(isinstance(h, LokiHandler) for h in sys_logger.handlers):
            sys_logger.addHandler(loki_handler)
            sys_logger.addFilter(trace_filter)

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
        
        # Trace ID 및 동적 태그 주입용 커스텀 필터 인스턴스 생성
        trace_filter = TraceIdFilter()
        
        # 로그 출력 포맷 지정 
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(threadName)s] %(levelname)-5s [%(trace_id)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
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
            tags={"application": "owls-pick-fastapi"},
            version="1",
        )
        loki_handler.setLevel(log_level)
        loki_handler.addFilter(trace_filter) # Loki 서버 전송 전 Trace ID 필터 등록
        loki_handler.setFormatter(formatter) # Trace ID가 포함된 포맷으로 전송 데이터 구성
        
        logger.addHandler(loki_handler)
        
        # 모듈 로거 생성 시 Uvicorn 및 FastAPI 전역 로거에도 핸들러 및 필터 바인딩
        attach_global_loki_handler(loki_handler, trace_filter)
        
    return logger