import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.getenv("GCP_PROJECT_ID"),
    location=os.getenv("GCP_LOCATION")
)

try:
    # 3.1 모델을 그대로 유지한 채 가장 가벼운 요청 송신
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents="connection test"
    )
    print("✅ 연결 성공! 응답:", response.text)
except Exception as e:
    print("❌ 연결 실패 에러 로그:")
    print(e)