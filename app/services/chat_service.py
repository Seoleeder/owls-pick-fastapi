#app\services\chat_service.py

import os
import json
import logging
from pathlib import Path
from google import genai
from google.genai import types
from app.schema.owls_chat_dto import QueryEmbeddingRequest, RagGenerationRequest
from app.utils.file_util import load_prompt_text, load_json_schema, load_prompt_template

logger = logging.getLogger(__name__)

class ChatService:
    """
    Owls 챗봇의 RAG 파이프라인(임베딩 및 답변 생성) 관리 서비스
    """
    
    def __init__(self):
        
        # 모델 설정 로드
        self.chat_model = os.getenv("CHAT_MODEL_NAME", "gemini-2.5-flash") 
        self.embedding_model = os.getenv("EMBEDDING_MODEL_NAME", "gemini-embedding-001")
        
        # 임베딩 벡터 및 작업 타입, 답변 생성 온도 환경 변수 로드
        self.output_dimension = int(os.getenv("EMBEDDING_OUTPUT_DIMENSION", "768"))
        self.task_type = os.getenv("EMBEDDING_QUERY_TASK_TYPE", "RETRIEVAL_QUERY")
        self.chat_temperature = float(os.getenv("CHAT_TEMPERATURE", "0.3"))
        
        # Vertex AI 프로젝트 및 리전 설정
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "asia-northeast3")
        
        # Vertex AI 클라이언트 초기화
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )
        
        # 시스템 프롬프트 및 응답 스키마 로드 
        self._load_resources()

    def _load_resources(self):
        """
        외부 파일로 분리된 프롬프트와 JSON 스키마 메모리 로드
        """
        # Owls 챗봇에 대한 시스템 프롬프트 및 JSON 스키마 로드
        self.system_instruction = load_prompt_text("chat_system.md")
        self.response_schema = load_json_schema("chat_response.json")
            
        # 메시지 재작성 및 챗봇 응답 생성 템플릿 로드
        self.rewrite_prompt_tmpl = load_prompt_template("chat_rewrite.md")
        self.generation_prompt_tmpl = load_prompt_template("chat_generation.md")

    async def extract_query_embedding(self, request: QueryEmbeddingRequest) -> list[float]:
        """
        사용자 메시지 기반 검색 최적화 벡터 추출
        """
        
        # 임베딩 대상 텍스트 초기화
        processed_message = request.user_message

        # 대화 내역 존재 여부 검증
        if request.history:
            # 대화 내역 리스트를 단일 텍스트 포맷으로 병합
            formatted_history = "\n".join([f"{h.role}: {h.content}" for h in request.history])
            
            # 재작성 템플릿에 대화 내역과 사용자 메시지 주입
            rewrite_prompt = self.rewrite_prompt_tmpl.format(
                history=formatted_history,
                user_message=request.user_message
            )
            
            try:
                # 생성 모델 호출 및 문맥 복원 메시지 재작성 수행
                rewrite_response = await self.client.aio.models.generate_content(
                    model=self.chat_model,
                    contents=rewrite_prompt
                )
                # 재작성 완료된 문자열 추출 및 공백 제거
                processed_message = rewrite_response.text.strip()
                
            except Exception as e:
                # 재작성 API 호출 실패 시 원본 메시지로 대체 (폴백 처리)
                logger.warning(f"[Rewriting Failed] Using original message: {e}")
                processed_message = request.user_message

        try:
            # 최종 메시지에 대한 임베딩 API 호출
            embedding_response = await self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=processed_message,
                config=types.EmbedContentConfig(
                    task_type=self.task_type,
                    output_dimensionality=self.output_dimension
                )
            )
            # 추출된 벡터 리스트 반환
            return embedding_response.embeddings[0].values
        except Exception as e:
            logger.error(f"[Embedding Failed] {str(e)}")
            raise e

    async def generate_chat_reply(self, request: RagGenerationRequest) -> str:
        """
        검색된 연관 게임 데이터와 대화 문맥 기반 최종 응답 생성
        """
        
        # [DEBUG] Context(게임 메타데이터) 상세 추적
        # Spring Boot에서 전달한 데이터가 누락 없이 도착했는지, LLM이 무엇을 읽는지 확인
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Starting Chat Generation with {len(request.contexts)} contexts.")
            for idx, context in enumerate(request.contexts):
                # 최대 100자까지만 잘라서 로깅
                text_preview = context[:100] + "..." if len(context) > 100 else context
                logger.debug(f"Context [{idx + 1}] Preview: {text_preview}")
        
        # 제공된 이전 대화 내역 문자열 포맷팅
        formatted_history = "\n".join([f"{h.role}: {h.content}" for h in request.history])
        
        # 벡터 검색으로 확보한 게임 메타데이터(Context) 구분자 결합
        formatted_context = "\n---\n".join(request.contexts)
        
        # 최종 응답 템플릿에 데이터 주입 및 프롬프트 조립 완성
        final_prompt = self.generation_prompt_tmpl.format(
            context=formatted_context,
            history=formatted_history,
            user_message=request.user_message
        )

        try:
            # 텍스트 생성 API 호출
            generation_response = await self.client.aio.models.generate_content(
                model=self.chat_model,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=self.chat_temperature,
                    response_mime_type="application/json",
                    response_schema=self.response_schema
                )
            )
            # JSON 응답 파싱
            response_data = json.loads(generation_response.text)
            
            reply_text = str(response_data.get("reply", ""))
            
            # 앞뒤 공백 제거 후 최종 답변 텍스트 반환
            return reply_text.strip()
            
        except Exception as e:
            logger.error(f"[Generation Failed] {str(e)}")
            raise e