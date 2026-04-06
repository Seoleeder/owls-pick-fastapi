from google.genai import types
from app.core.gemini_config import SAFETY_SETTINGS_BLOCK_NONE

class ReviewConfigFactory:
    """
    스팀 리뷰 스코어 기반의 동적 GenerateContentConfig 생성 팩토리
    """
    
    @staticmethod
    def create_config(
        review_score: int,
        base_instruction: str,
        response_schema: dict,
        temperature: float
    ) -> types.GenerateContentConfig:
        
        # 평가 분포별 요약 가이드라인 설정
        dynamic_rule = f"\n\n[데이터 요약 기준]\n스팀 공식 평가 지표 등급: {review_score}\n\n[작성 지침]\n"

        # 스팀 공식 평가 등급 ID 매핑 (1~9)
        if review_score == 9:
            # 9: 압도적으로 긍정적 (Overwhelmingly Positive)
            dynamic_rule += "게이머들의 극찬과 열광적인 반응을 최우선으로 강조하여 요약. 단점은 리뷰 데이터에 매우 뚜렷하고 반복적으로 나타날 경우에 한해서만 극히 제한적으로 언급할 것."
            
        elif review_score == 8:
            # 8: 매우 긍정적 (Very Positive)
            dynamic_rule += "강력한 호평 위주로 요약하되, 게임을 즐긴 유저들도 공통적으로 지적하는 '사소한 아쉬움'이나 '옥에 티'가 있다면 1문장 정도로 포함할 것."
            
        elif review_score in (6, 7):
            # 6, 7: 대체로 긍정적, 긍정적 (Mostly Positive / Positive)
            dynamic_rule += "전반적으로는 추천하는 여론이지만, 구매 전 반드시 알아둬야 할 명확한 단점이나 진입장벽(호불호 요소)이 존재하므로 이를 객관적이고 비중 있게 병기할 것."
            
        elif review_score == 5:
            # 5: 복합적 (Mixed)
            dynamic_rule += "유저들 사이에서 호불호가 극명하게 갈리는 상태. 칭찬받는 장점과 비판받는 단점을 5:5 비율로 팽팽하고 균형감 있게 대조하여 어느 한쪽으로도 편향되지 않게 요약할 것."
            
        elif review_score in (3, 4):
            # 3, 4: 부정적, 대체로 부정적 (Negative / Mostly Negative)
            dynamic_rule += "최적화, 버그, 콘텐츠 부족 등 유저들이 비판하는 핵심적인 문제점을 중심으로 요약. 단, 특정 취향의 유저들이 호평하는 '최소한의 장점'이 있다면 1문장 정도로 간략히 포함할 것."
            
        elif review_score == 2:
            # 2: 매우 부정적 (Very Negative)
            dynamic_rule += "혹평과 실망스러운 여론을 중심으로 게임의 구조적, 기술적 문제점을 강도 높게 요약. 긍정적인 의견은 거의 없으므로 억지로 장점을 지어내어 포장하지 말 것."
            
        elif review_score == 1:
            # 1: 압도적으로 부정적 (Overwhelmingly Negative)
            dynamic_rule += "게임의 치명적인 결함과 유저들의 분노 여론을 있는 그대로 신랄하게 요약. 장점에 대한 언급은 절대 배제하고 어떤 이유로 참사가 일어났는지 원인 파악에 집중할 것."
            
        else:
            # 0 또는 예외값 (평가 없음 등)
            dynamic_rule += "데이터에 나타난 유저들의 반응을 편견 없이 있는 그대로 객관적으로 요약할 것."

        # 최종 설정 객체 빌드
        return types.GenerateContentConfig(
            system_instruction=base_instruction + dynamic_rule,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema, 
            safety_settings=SAFETY_SETTINGS_BLOCK_NONE
        )
        