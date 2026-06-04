from pydantic import BaseModel

# 추천 요청 모델
class ReqRecommend(BaseModel):
    regionCode: str
    startDate: str
    endDate: str
    type: str