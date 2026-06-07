from pydantic import BaseModel

# 추천 요청 모델
class RecommendRequest(BaseModel):
    areaCode: str
    startDate: str
    endDate: str
    type: str