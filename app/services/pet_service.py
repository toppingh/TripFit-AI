from app.services.req_api_service import req_area_list_api


async def get_pet_list_and_filtered(city_code, state_code) -> dict:
    data = await req_area_list_api(
        "KorPetTourService2/areaBasedList2", {
            "lDongRegnCd": city_code,
            "lDongSignguCd": state_code
        }
    )
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

        # 76-관광지, 78-문화시설, 79-쇼핑
        if cnt_id in ["76", "78", "79"]:
            filtered["spots"].append(places)
        # 82-음식점
        elif cnt_id == "76":
            filtered["eats"].append(places)
        # 80-숙박
        elif cnt_id == "80":
            filtered["hotels"].append(places)

    return filtered