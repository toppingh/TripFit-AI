from fastapi import APIRouter

router = APIRouter()

@router.post("/recommend")
def recommend():
    return {
        "result": "추천 결과"
    }