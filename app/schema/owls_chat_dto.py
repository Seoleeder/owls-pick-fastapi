#app\schema\owls_chat_dto.py

from app.schema.base_dto import CamelModel

class ChatHistoryDto(CamelModel):
    """
    최근 대화 내역 DTO
    """
    role: str
    content: str

class QueryEmbeddingRequest(CamelModel):
    """
    유저 발화 벡터 임베딩 요청 DTO
    """
    history: list[ChatHistoryDto] = []
    user_message: str

class QueryEmbeddingResponse(CamelModel):
    """
    유저 발화 벡터 임베딩 응답 DTO
    """
    vector: list[float]

class RagGenerationRequest(CamelModel):
    """
    RAG 기반 최종 답변 생성 요청 DTO
    """
    history: list[ChatHistoryDto] = []
    user_message: str
    contexts: list[str]

class RagGenerationResponse(CamelModel):
    """
    RAG 기반 최종 답변 생성 응답 DTO
    """
    reply: str