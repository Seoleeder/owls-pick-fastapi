import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 환경변수 및 API 키 세팅
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 2. FastAPI 앱 생성
app = FastAPI(title="Owl's Pick AI Engine")

# ==========================================
# 🎯 최적의 AI 모델 세팅
# ==========================================
# 생성 모델: 번역 워커 & RAG 챗봇 응답용 (가장 빠르고 가성비 좋은 최신 Flash)
GENERATION_MODEL = "gemini-3.1-flash-preview"
model = genai.GenerativeModel(GENERATION_MODEL)

# 임베딩 모델: 텍스트를 벡터 숫자 배열로 변환 (pgvector 저장용)
EMBEDDING_MODEL = "models/text-embedding-004"


# ==========================================
# 📦 DTO (요청 데이터 규격 정의)
# ==========================================
class TextRequest(BaseModel):
    text: str


# ==========================================
# 🚀 API 엔드포인트 (Controller)
# ==========================================
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Owl's Pick AI Engine이 정상 가동 중입니다."}

# [기능 1] 번역기 & 챗봇 응답 테스트 (Flash 모델)
@app.post("/api/generate")
async def generate_text(req: TextRequest):
    try:
        # Spring Boot에서 넘어온 텍스트(또는 프롬프트)를 모델에 전달
        response = model.generate_content(req.text)
        return {"success": True, "result": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# [기능 2] 임베딩 테스트 (text-embedding-004 모델)
@app.post("/api/embed")
async def create_embedding(req: TextRequest):
    try:
        # 텍스트를 벡터(숫자 배열)로 변환
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=req.text,
            task_type="retrieval_document" # RAG 검색용 문서라는 것을 명시
        )
        
        vector = result['embedding'] # 변환된 숫자 배열
        
        return {
            "success": True,
            "original_text": req.text,
            "vector_length": len(vector), # 보통 768개의 숫자가 나옴
            "vector_preview": vector[:5]  # 너무 기니까 앞의 5개 숫자만 미리보기
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))