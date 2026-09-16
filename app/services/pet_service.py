import logging

from app.services.req_api_service import req_area_list_api

logger = logging.getLogger("tripfit.pet_service")

# 디버그 출력용 함수
def log_category_details(category_name, items, max: int = 10):
    logger.info(f"[{category_name}] 총 {len(items)}건")

    if not items:
        logger.info(f"{category_name} 데이터가 존재하지 않습니다.")
        return

    for idx, i in enumerate(items[:max], 1):
        name = i.get("name") or "이름 없음"
        addr = i.get("address") or "주소 없음"
        logger.info(f"{idx}. {name} | 주소 : {addr}")

    if len(items) > max:
        logger.info(f"... 외 {len(items) - max}개 항목은 생략")

async def get_pet_list_and_filtered(city_code, state_code) -> dict:
    # debug 로그
    logger.info(f"[PET] 반려동물 관광정보 API 호출 - city: {city_code}, state: {state_code}")

    # 파라미터 설정
    params = {
        "lDongRegnCd": city_code
    }

    # 시군구 값 확인 후 파라미터 추가
    if state_code and str(state_code).strip():
        params["lDongSignguCd"] = state_code

    # params 전달
    data = await req_area_list_api(
        "KorPetTourService2/areaBasedList2", 
        params
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
            "mapy": item.get("mapy"),
            "img": item.get("firstimage")
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
    log_category_details("관광지", filtered["spots"])
    log_category_details("식당", filtered["eats"])
    log_category_details("숙박", filtered["hotels"])


    return filtered