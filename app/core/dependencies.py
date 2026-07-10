#app\core\dependencies.py

import os
from openai import AsyncOpenAI

# OpenAI 클라이언트 전역 인스턴스
_openai_client: AsyncOpenAI | None = None

def get_openai_client() -> AsyncOpenAI:
    """
    OpenAI 클라이언트 의존성 주입 함수
    """
    global _openai_client
    if _openai_client is None:
        # 환경 변수에서 API 키 로드 및 객체 초기화
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client