from app.services.req_api_service import req_detail_tour_api


# content_id에 해당하는 관광지의 상세 정보 데이터 호출
async def get_area_detail_info(content_id) -> dict:
    return await req_detail_tour_api(content_id)