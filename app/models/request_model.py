from datetime import date
from typing import List
from pydantic import BaseModel, Field


# Next.js(백엔드) -> AI 서버 요청 구조 정의
class CourseRequest(BaseModel):
    cityCode: str = Field(..., description="법정동 시도 코드")
    stateCode: str = Field(..., description="법정동 시군구 코드")
    startDate: date = Field(..., description="여행 시작 날짜")
    endDate: date = Field(..., description="여행 종료 날짜")
    partnerType: str = Field(..., description="동반자 유형 (WHEELCHAIR, BABY, PET, ELDERLY")

    # 여행 총 일수 계산 함수
    @property
    def total_trip(self) -> int:
        # 당일치기 = 1일, 1박 = 2일
        days = self.endDate - self.startDate
        return max(1, days.days + 1)

# 관광지 추천 응답 구조 정의
class SpotDetail(BaseModel):
    time: str = Field(..., description="관광지 방문 시간 (13:00)")
    type: str = Field(..., description="장소 타입 (관광지, 숙박, 식당")
    name: str = Field(..., description="장소 이름")
    address: str = Field(..., description="주소")
    mapx: str = Field(..., description="경도")
    mapy: str = Field(..., description="위도")
    reason: str = Field(..., description="코스 추천 이유 (Gemini 응답)")
    tip: str = Field(..., description="교통약자 맞춤 팁")

# 일자별 코스 구조 정의
class DailyRoute(BaseModel):
     day: int = Field(..., description="여행 일자")
     date: str = Field(..., description="날짜 (YYYY-MM-DD)")
     spots: List[SpotDetail] = Field(..., description="시간순으로 추천 코스(일정) 배열")

# Next.js(백엔드) <- AI 서버 관광지 추천 최종 응답 구조 정의
class CourseResponse(BaseModel):
    partnerType: str
    totalDays: int
    summary: str = Field(..., description="추천 코스 요약")
    routes: List[DailyRoute] = Field(..., description="일자별 스케줄")