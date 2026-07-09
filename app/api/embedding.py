#app\api\embedding.py

import traceback
from fastapi import APIRouter, HTTPException, Depends

from app.schema.dto.embedding_dto import EmbeddingBatchRequest, EmbeddingBatchResponse
from app.services.embedding_service import EmbeddingService
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

def get_embedding_service() -> EmbeddingService:
    """
    EmbeddingService 의존성 주입(DI)용 팩토리 함수
    """
    return EmbeddingService()

@router.post("/batch", response_model=EmbeddingBatchResponse)
async def generate_batch_embeddings(
    req: EmbeddingBatchRequest,
    service: EmbeddingService = Depends(get_embedding_service)
    ):
    """
    게임 메타데이터 배치 임베딩 생성 API
    """
    logger.info(f"Received Request: Batch Embedding for {len(req.games)} games.")
    
    try:
        # 서비스 계층 호출 및 배치 처리
        result = await service.generate_embeddings(req.games)
        logger.info(f"Batch Embedding Completed for {len(req.games)} games.")
        
        return EmbeddingBatchResponse(results=result)
        
    except Exception as e:
        # 내부 로직 실패 시 HTTP 500 에러를 반환
        logger.error(f"Python Internal Error (Embedding):\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))