from typing import List, Optional
from pydantic import BaseModel, Field

# Gemini 응답 JSON 스키마로 고정 -> Pydantic 모델
class PlaceList(BaseModel):
    name: str = Field(description="장소명")
    address: Optional[str] = Field(default="", description="상세 주소")
    mapx: Optional[str] = Field(default="", description="경도")
    mapy: Optional[str] = Field(default="", description="위도")
    img: Optional[str] = Field(default="", description="이미지 URL")
    description: str = Field(description="추천 이유 요약")

class DayList(BaseModel):
    day_number: int = Field(description="일차 (ex. 1박2일중 몇일차인지)")
    date: str = Field(description="추천 방문 날짜 (형식: YYYY-MM-DD)")
    places: List[PlaceList] = Field(description="추천 장소 목록")

class FinalCourseResponse(BaseModel):
    title: str = Field(description="여행 제목")
    days: List[DayList] = Field(description="일자별 코스 목록")