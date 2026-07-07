#app\api\localization.py

import traceback
from fastapi import APIRouter
from app.schema.dto.localization_dto import BulkLocalizationRequest, BulkLocalizationResponse
from app.services.localization_service import LocalizationService
from app.core.logger import setup_logger
from fastapi import HTTPException

logger = setup_logger(__name__)
router = APIRouter()

# 서비스 인스턴스 싱글톤(Singleton) 생성
localization_service = LocalizationService()

@router.post("/games/bulk", response_model=BulkLocalizationResponse)
async def localize_bulk_games(req: BulkLocalizationRequest):
    """
    대량 게임 데이터 한글화 API
    OpenAI 기반의 비동기 병렬 처리를 통해 대량의 게임 데이터를 번역하여 반환
    """
    game_count = len(req.games)
    logger.info(f"Received Request: Bulk Localization for {game_count} games.")
    
    try:
        # 비동기 병렬 한글화 처리 위임
        results = await localization_service.process_bulk_localizations(req.games)
        
        logger.info(f"Localization Completed: Returning {len(results)} results.")
        
        return BulkLocalizationResponse(success=True, results=results)
    
    except Exception as e:
        logger.error(f"Python Internal Error (Game Localization):\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))    




