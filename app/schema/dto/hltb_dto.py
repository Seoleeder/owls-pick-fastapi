#app\schema\hltb_dto.py

from enum import Enum
from app.schema.dto.base_dto import CamelModel

# ==========================================
# [HLTB Sync Status Enum] 동기화 상태값
# ==========================================
class SyncStatus(str, Enum):
    UNSYNCED = "UNSYNCED"
    SUCCESS = "SUCCESS"
    NO_DATA = "NO_DATA"    
    NOT_FOUND = "NOT_FOUND" 
    FAILED = "FAILED"

# ==========================================
# [HLTB Sync Response] 플레이타임 수집 DTO
# ==========================================

class HltbSyncResponse(CamelModel):
    """
    FastAPI -> Spring Boot HLTB 플레이타임 결과 응답 모델
    (Spring Boot 측에서 Double로 받아 분 단위로 직접 변환함)
    """
    main_story: float | None = None
    main_extra: float | None = None
    completionist: float | None = None
    status: str