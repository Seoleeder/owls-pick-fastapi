from enum import Enum

class GenaiFailReason(str, Enum):
    """
    GenAI 파이프라인에서 공통으로 사용하는 실패 사유 ENUM
    """
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"       # 유효 데이터 부족
    SAFETY_FILTER_REJECTED = "SAFETY_FILTER_REJECTED" # 모델 안전 정책 위반으로 인한 처리 거부
    NETWORK_ERROR = "NETWORK_ERROR"             # API 통신 장애 및 타임아웃
    INVALID_RESPONSE = "INVALID_RESPONSE"          # 파싱 불가 등 비정상 응답 구조
    UNKNOWN_ERROR = "UNKNOWN_ERROR"             # 기타 예기치 못한 시스템 오류