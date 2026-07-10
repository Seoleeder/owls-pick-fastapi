#app\api\localization.py

import traceback
from openai import AsyncOpenAI
from fastapi import APIRouter, Depends
from app.schema.dto.localization_dto import BulkLocalizationRequest, BulkLocalizationResponse
from app.services.localization_service import LocalizationService
from app.core.dependencies import get_openai_client
from app.core.logger import setup_logger
from fastapi import HTTPException

logger = setup_logger(__name__)
router = APIRouter()

def get_localization_service(
    client: AsyncOpenAI = Depends(get_openai_client)
) -> LocalizationService:
    """
    LocalizationService 의존성 주입(DI)용 팩토리 함수
    """
    return LocalizationService(client=client)

@router.post("/games/bulk", response_model=BulkLocalizationResponse)
async def localize_bulk_games(
    req: BulkLocalizationRequest,
    service: LocalizationService = Depends(get_localization_service)
    ):
    """
    대량 게임 데이터 한글화 API
    OpenAI 기반의 비동기 병렬 처리를 통한 대량 데이터 한글화 수행 및 결과 반환
    """
    game_count = len(req.games)
    logger.info(f"Received Request: Bulk Localization for {game_count} games.")
    
    try:
        # 비동기 병렬 한글화 처리 위임
        results = await service.process_bulk_localizations(req.games)
        
        logger.info(f"Localization Completed: Returning {len(results)} results.")
        
        return BulkLocalizationResponse(success=True, results=results)
    
    except Exception as e:
        logger.error(f"Python Internal Error (Game Localization):\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))    




