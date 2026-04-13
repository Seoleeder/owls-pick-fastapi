from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    """
    자동 camelCase 변환 공통 부모 모델
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )