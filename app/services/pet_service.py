import logging

from app.services.req_api_service import req_area_list_api

logger = logging.getLogger("tripfit.pet_service")

async def get_pet_list_and_filtered(city_code, state_code) -> dict:
    # debug 로그
    logger.info(f"[PET] 반려동물 관광정보 API 호출 - city: {city_code}, state: {state_code}")

    data = await req_area_list_api(
        "KorPetTourService2/areaBasedList2", {
            "lDongRegnCd": city_code,
            "lDongSignguCd": state_code
        }
    )

    # debug 로그
    logger.info(f"[PET] API 원본 데이터 수집 결과 - 총 {len(data) if data else 0}건")

    filtered = {"spots": [], "eats": [], "hotels": []}

    for item in data:
        # api 응답에서 contenttypeid 기준으로 필터링
        cnt_id = item.get("contenttypeid")

        places = {
            "name": item.get("title"),
            "address": item.get("addr1"),
            "mapx": item.get("mapx"),
            "mapy": item.get("mapy")
        }

        # 12-관광지, 14-문화시설, 38-쇼핑
        if cnt_id in ["12", "14", "38"]:
            filtered["spots"].append(places)
        # 39-음식점
        elif cnt_id == "39":
            filtered["eats"].append(places)
        # 32-숙박
        elif cnt_id == "32":
            filtered["hotels"].append(places)
    # debug 로그
    logger.info(f"[PET] 1차 분류(필터링) 결과 - 관광지: {len(filtered['spots'])}건, 식당: {len(filtered['eats'])}건, 숙박: {len(filtered['hotels'])}건")

    return filtered