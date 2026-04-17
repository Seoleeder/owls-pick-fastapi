import traceback
from typing import List
from fastapi import APIRouter, HTTPException

from app.schema.embedding_dto import EmbeddingBatchRequest, EmbeddingBatchResponse
from app.services.embedding_service import EmbeddingService
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# 싱글톤 서비스 인스턴스
embedding_service = EmbeddingService()

@router.post("/batch", response_model=EmbeddingBatchResponse)
async def generate_batch_embeddings(req: EmbeddingBatchRequest):
    """
    게임 메타데이터 배치 임베딩 생성 API
    """
    logger.info(f"Received Request: Batch Embedding for {len(req.games)} games.")
    
    try:
        # 서비스 계층 호출 및 배치 처리
        result = await embedding_service.process_batch(req.games)
        logger.info(f"Batch Embedding Completed for {len(req.games)} games.")
        
        return EmbeddingBatchResponse(results=result)
        
    except Exception as e:
        # 내부 로직 실패 시 HTTP 500 에러를 반환
        logger.error(f"Python Internal Error (Embedding):\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))