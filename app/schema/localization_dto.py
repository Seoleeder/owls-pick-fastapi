#app\schema\localization_dto.py

from pydantic import BaseModel
from typing import List, Optional

# ==========================================
# [Localization Request/Response] 설명/스토리라인 한글화 DTO
# ==========================================

# [Request] Spring Boot -> FastAPI (요청 DTO)

class GameItem(BaseModel):
    """단일 게임 데이터 요청 모델"""
    game_id: int
    description: str | None = None
    storyline: str | None = None


class BulkLocalizationRequest(BaseModel):
    """대량 게임 데이터 한글화 요청 모델"""
    games: List[GameItem]


# [Response] FastAPI -> Spring Boot (응답 DTO)

class LocalizationResult(BaseModel):
    """단일 게임 한글화 응답 모델"""
    game_id: int
    description_ko: str | None = None
    storyline_ko: str | None = None

class BulkLocalizationResponse(BaseModel):
    """대량 게임 한글화 응답 모델"""
    success: bool
    results: List[LocalizationResult]
    

# ==========================================
# [Keyword Request/Response] 키워드 한글화 DTO
# ==========================================

class KeywordLocalizationRequest(BaseModel):
    """키워드 대량 번역 요청 모델"""
    keywords: List[str]

class KeywordResult(BaseModel):
    """단일 키워드 한글화 응답 모델"""
    engName: str
    korName: str | None = None

class BulkKeywordLocalizationResponse(BaseModel):
    """키워드 대량 한글화 응답 모델"""
    localizationResults: List[KeywordResult]