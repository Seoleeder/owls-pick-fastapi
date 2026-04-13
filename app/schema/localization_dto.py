#app\schema\localization_dto.py

from app.schema.base_dto import CamelModel
from typing import List


# ==========================================
# [Localization Request/Response] 설명/스토리라인 한글화 DTO
# ==========================================

# [Request] Spring Boot -> FastAPI (요청 DTO)

class GameItem(CamelModel):
    """단일 게임 데이터 요청 모델"""
    game_id: int
    description: str | None = None
    storyline: str | None = None


class BulkLocalizationRequest(CamelModel):
    """대량 게임 데이터 한글화 요청 모델"""
    games: List[GameItem]


# [Response] FastAPI -> Spring Boot (응답 DTO)

class LocalizationResult(CamelModel):
    """단일 게임 한글화 응답 모델"""
    game_id: int
    description_ko: str | None = None
    storyline_ko: str | None = None

class BulkLocalizationResponse(CamelModel):
    """대량 게임 한글화 응답 모델"""
    success: bool
    results: List[LocalizationResult]
    

# ==========================================
# [Keyword Request/Response] 키워드 한글화 DTO
# ==========================================

class KeywordLocalizationRequest(CamelModel):
    """키워드 대량 번역 요청 모델"""
    keywords: List[str]

class KeywordResult(CamelModel):
    """단일 키워드 한글화 응답 모델"""
    eng_name: str
    kor_name: str | None = None

class BulkKeywordLocalizationResponse(CamelModel):
    """키워드 대량 한글화 응답 모델"""
    localization_results: List[KeywordResult]