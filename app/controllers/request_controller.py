from fastapi import APIRouter, HTTPException

from app.models.request_model import CourseResponse, CourseRequest
from app.services.course_service import create_tripfit_course

router = APIRouter()

@router.post("/cousre", response_model=CourseResponse)
async def create_recommendation_course(payload: CourseRequest):
    try:
        course_result = await create_tripfit_course(
            city_code=payload.cityCode,
            state_code=payload.stateCode,
            type=payload.partnerType,
            start_date=payload.startDate,
            end_date=payload.endDate,
            total_days=payload.total_trip
        )

        if "error" in course_result:
            raise HTTPException(status_code=400, detail=course_result["error"])
        return course_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))