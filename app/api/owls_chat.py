import traceback
from fastapi import APIRouter, HTTPException

from app.schema.owls_chat_dto import (
    QueryEmbeddingRequest, QueryEmbeddingResponse,
    RagGenerationRequest, RagGenerationResponse
)
from app.services.chat_service import ChatService
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# 싱글톤 서비스 인스턴스 초기화
chat_service = ChatService()

@router.post("/embeddings/query", response_model=QueryEmbeddingResponse)
async def generate_query_embedding(req: QueryEmbeddingRequest):
    """
    RAG 검색을 위한 사용자 메시지 벡터 임베딩 API
    """
    logger.info(f"Received Request: Query Embedding (History Length: {len(req.history)})")
    
    try:
        # 서비스 계층 호출 및 검색용 벡터 추출
        vector = await chat_service.extract_query_embedding(req)
        logger.info("Query Embedding Completed Successfully.")
        
        return QueryEmbeddingResponse(vector=vector)
        
    except Exception as e:
        # 내부 로직 실패 시 HTTP 500 에러 및 로깅 처리
        logger.error(f"Python Internal Error (Query Embedding):\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to generate query embedding")


@router.post("/generate", response_model=RagGenerationResponse)
async def generate_rag_chat(req: RagGenerationRequest):
    """
    검색된 연관 게임 데이터 기반 챗봇 최종 응답 생성 API
    """
    logger.info(f"Received Request: Chat Generation (Contexts Length: {len(req.contexts)})")
    
    try:
        # 서비스 계층 호출 및 최종 텍스트 응답 생성
        reply = await chat_service.generate_chat_reply(req)
        logger.info("Chat Generation Completed Successfully.")
        
        return RagGenerationResponse(reply=reply)
        
    except Exception as e:
        # 내부 로직 실패 시 HTTP 500 에러 및 로깅 처리
        logger.error(f"Python Internal Error (Chat Generation):\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to generate chat reply")