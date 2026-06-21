import httpx
from app.config.settings import settings

# 무장애 여행 지역 기반 조회 API 호출 구조 정의
async def req_area_list_api(endpoint: str, params: dict) -> list:
    endpoint = f"{settings.BASE_URL}/{endpoint}"
    params = {
        "serviceKey": settings.TOUR_API_KEY,
        "MobileOS": settings.MOBILE_OS,
        "MobileApp": settings.MOBILE_APP,
        "_type": settings.TYPE,
        "numOfRows": 40, # 필수 x -> 대기 시간 단축을 위해 추가
        "pageNo": 1, # 필수 x -> 대기 시간 단축을 위해 추가
        **params
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, params=params, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
                return [items] if isinstance(items, dict) else items
            return []
        except Exception as e:
            print(f"[API 조회 에러] : {e}")
            return []

# 무장애 여행 상세 정보 조회 API 호출 구조 정의
async def req_detail_tour_api(content_id:str) -> dict:
    endpoint = f"{settings.BASE_URL}/detailWithTour2"
    params = {
        "serviceKey": settings.TOUR_API_KEY,
        "MobileOS": settings.MOBILE_OS,
        "MobileApp": settings.MOBILE_APP,
        "_type": settings.TYPE,
        "content_id": content_id
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, params=params, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                items = data.get("response", {}).get("body", {}).get("items", [])
                return items[0] if isinstance(items, dict) else items
            return {}
        except Exception as e:
            print(f"[API 상세 조회 에러 Id : {content_id}] : {e}")
            return {}
