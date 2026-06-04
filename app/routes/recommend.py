from fastapi import APIRouter

from app.models.recommend import ReqRecommend
from app.services.gemini_service import trip_course_create
from app.services.tourism_service import get_tour_place

router = APIRouter()

@router.post("/course")
async def recommend(req: ReqRecommend):
    places = get_tour_place(req.regionCode)

    prompt = f"""
    너는 이동 약자를 동반한 여행자에게 코스를 추천하는 여행 전문가다.
    아래 [여행정보]는 현재 코스 추천을 받기 위해 여행자가 입력한 정보이고, 이 [여행정보]의 정보를 기반으로 날짜별 여행 코스를 생성해야 한다.
    
    [여행정보]
    여행 지역 코드 : {req.regionCode}
    여행 기간 : {req.startDate}부터 {req.endDate}
    동반자 유형 : {req.type}
    관광지 후보 : {places}
    
    답변은 반드시 보기 좋게 작성해야 한다.    
    """
    result = trip_course_create(prompt)

    return {
        "success": True,
        "result": result
    }