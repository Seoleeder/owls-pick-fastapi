#app\schema\embedding_dto.py

from enum import Enum
from app.schema.base_dto import CamelModel

# ==========================================
# [Embedding Status Enum] 벡터 임베딩 상태값
# ==========================================

class EmbeddingStatus(str, Enum):
    UNEMBEDDED = "UNEMBEDDED" # 파이프라인 진입 전 
    SUCCESS = "SUCCESS"       # 임베딩 성공 
    FAILED = "FAILED"         # 임베딩 실패 (타임아웃, 모델 에러 등 일시적 오류)

# ==========================================
# [Embedding Request] 게임 메타데이터 청크 요청 DTO
# ==========================================

class RawGameData(CamelModel):
    """
    Spring Boot -> FastAPI 임베딩 원본 데이터 DTO
    """
    game_id: int
    title: str
    description: str | None = None
    genres: list[str] = []
    themes: list[str] = []
    keywords: list[str] = []
    main_story: int | None = None
    review_score_desc: str | None = None
    review_summary: str | None = None

class EmbeddingBatchRequest(CamelModel):
    """
    배치 단위 임베딩 요청 DTO
    """
    games: list[RawGameData]

# ==========================================
# [Embedding Response] 벡터 임베딩 결과 응답 DTO
# ==========================================

class EmbeddingResult(CamelModel):
    """
    단일 게임 벡터 임베딩 결과 DTO
    """
    game_id: int
    vector: list[float] | None = None
    source_text: str
    status: str

class EmbeddingBatchResponse(CamelModel):
    """
    FastAPI -> Spring Boot 임베딩 배치 결과 응답 DTO
    """
    results: list[EmbeddingResult]