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
async def req_detail_tour_api(client: httpx.AsyncClient, content_id:str) -> dict:
    endpoint = f"{settings.BASE_URL}/KorWithService2/detailWithTour2"

    params = {
        "serviceKey": settings.TOUR_API_KEY,
        "MobileOS": settings.MOBILE_OS,
        "MobileApp": settings.MOBILE_APP,
        "_type": settings.TYPE,
        "contentId": content_id
    }

    try:
        # 💡 매번 새로 생성하지 않고, 전달받은 세션(client)을 그대로 재사용하여 요청합니다.
        response = await client.get(endpoint, params=params, timeout=10.0)

        if response.status_code == 200:
            raw_data = response.json()
            response_obj = raw_data.get("response", {})
            body_obj = response_obj.get("body", {})
            items_obj = body_obj.get("items", {})
            item_data = items_obj.get("item", [])

            if isinstance(item_data, list) and len(item_data) > 0:
                return item_data[0]
            elif isinstance(item_data, dict):
                return item_data

            return raw_data

        print(f"[상세조회 API 호출 에러] Status: {response.status_code} (Id: {content_id})")
        return {}
    except Exception as e:
        print(f"[API 상세 조회 크래시 에러 Id : {content_id}] 이유: {e}")
        return {}