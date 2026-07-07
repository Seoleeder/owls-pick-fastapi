#app\schema\owls_chat_dto.py

from pydantic import Field
from app.schema.dto.base_dto import CamelModel

class ChatHistoryDto(CamelModel):
    """
    최근 대화 내역 DTO
    """
    role: str = Field(
        ...,
        description="발화자 역할 (USER 또는 ASSISTANT)"
    )
    content: str = Field(
        ...,
        description="대화 내용"
    )

class QueryEmbeddingRequest(CamelModel):
    """
    유저 발화 벡터 임베딩 요청 DTO
    """
    history: list[ChatHistoryDto] = Field(
        default_factory=list,
        description="최근 대화 내역 배열"
    )
    user_message: str = Field(
        ..., 
        min_length=1, 
        description="사용자의 현재 질문",
        json_schema_extra={"errorMessage": "User message must not be empty."}
    )

class QueryEmbeddingResponse(CamelModel):
    """
    유저 발화 벡터 임베딩 응답 DTO
    """
    vector: list[float] = Field(
        ..., description="독립 검색어 기반 추출된 768차원 벡터 배열"
    )

class RagGenerationRequest(CamelModel):
    """
    RAG 기반 최종 답변 생성 요청 DTO
    """
    history: list[ChatHistoryDto] = Field(
        default_factory=list,
        description="최근 대화 내역 배열"
    )
    user_message: str = Field(
        ..., 
        min_length=1, 
        description="사용자의 현재 질문",
        json_schema_extra={"errorMessage": "User message must not be empty."}
    )
    contexts: list[str] = Field(
        ...,
        description="Vector DB에서 검색된 유사 게임 원본 메타데이터 배열"
    )

class RagGenerationResponse(CamelModel):
    """
    RAG 기반 최종 답변 생성 응답 DTO
    """
    reply: str = Field(
        ...,
        description="RAG 파이프라인을 통해 생성된 최종 챗봇 답변"
    )
    
class TitleGenerationRequest(CamelModel):
    """
    세션 제목 자동 요약 요청 DTO
    """
    user_message: str = Field(
        ..., 
        min_length=1, 
        description="채팅 세션의 첫 유저 발화문",
        json_schema_extra={"errorMessage": "User message must not be empty."}
    )

class TitleGenerationResponse(CamelModel):
    """
    세션 제목 자동 요약 응답 DTO
    """
    title: str = Field(..., description="생성된 세션 제목 (30자 이내 제한)")