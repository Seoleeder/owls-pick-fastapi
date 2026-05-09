import contextvars
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# 현재 API 요청의 Trace ID 보관용 비동기 컨텍스트 변수 (기본값: "-")
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")

class TraceIdMiddleware(BaseHTTPMiddleware):
    
    # HTTP 요청을 가로채어 Trace ID 추출 및 컨텍스트 바인딩 수행
    async def dispatch(self, request: Request, call_next):
        
        # W3C 분산 추적 표준 헤더 조회
        traceparent = request.headers.get("traceparent")
        
        # 표준 규격(00-traceid-spanid-01) 검증 및 실제 Trace ID(고유 난수) 부분만 추출
        if traceparent and len(traceparent.split("-")) >= 3:
            trace_id = traceparent.split("-")[1]
        else:
            # 표준 헤더 부재 시 B3 헤더 확인 및 신규 UUID 발급
            trace_id = request.headers.get("X-B3-TraceId", uuid.uuid4().hex)

        # 컨텍스트 변수에 Trace ID 바인딩 및 복구용 키(token) 확보
        token = trace_id_var.set(trace_id)

        try:
            # 실제 비즈니스 로직 수행 및 응답(Response) 객체 반환 대기
            response = await call_next(request)
            
            # HTTP 응답 헤더에 Trace ID 명시
            response.headers["X-Trace-Id"] = trace_id
            return response
            
        finally:
            # 메모리 누수 방지를 위한 컨텍스트 초기화
            trace_id_var.reset(token)