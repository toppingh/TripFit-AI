from pyasn1_modules.rfc7773 import e_legnamnden

from app.services.req_api_service import req_area_list_api


async def get_disability_list_and_filtered(city_code: str, state_code: str) -> dict:
    data = await req_area_list_api(
        "KorWithService2/areaBasedList2",
        {
            "lDongRegnCd": city_code,
            "lDongSignguCd": state_code
        }
    )

    filtered = {"spots": [], "eats": [], "hotels": []}

    for item in data:
        cnt_id = item.get("contenttypeid")

        # 12-관광지, 14-문화시설, 15-행사/축제/공연, 38-쇼핑
        if cnt_id in ["12", "14", "15", "38"]:
            filtered["spots"].append(item)
        # 39-음식점
        elif cnt_id == "39":
            filtered["eats"].append(item)
        # 32-숙박
        elif cnt_id == "32":
            filtered["hotels"].append(item)
    return filtered

# 호출한 api 응답 구조 중 필드 값이 None 이거나 "없음"일 경우를 방지하는 함수
def is_blank(val):
    return val is None or val == "" or val == "없음" in str(val)

# 첫번째 api 호출(지역기반 정보 api) 후 응답 값 -> detailWithTour2 api 호출 후 상세 정보를 받아 동반자 유형별로 적합한 장소만 필터링
def filtered_partner_type(detail: dict, type:str) -> dict:
    if not detail:
        return {}

    # 지체장애(휠체어 동반) 그룹 필드 필터링
    if type == "WHEELCHAIR":
        parking = detail.get("parking") # 장애인 주차장
        route = detail.get("route") # 접근로 (경사로)
        wheelchair = detail.get("wheelchair") # 휠체어 대여
        exit = detail.get("exit") # 출입통로 (경사로)
        elevator = detail.get("elevator") # 엘리베이터
        restroom = detail.get("restroom") # 장애인 화장실

        # 부/적합 판단 기준
        # 장애인 주차장, 경사로, 엘리베이터, 장애인 화장실이 없으면 부적합
        if is_blank(parking) or is_blank(route) or is_blank(exit) or is_blank(elevator) or is_blank(restroom):
            return {}

        return {
            "parking": parking, # 장애인 주차장
            "publieTransport": detail.get("publiedTransport"), # 대중교통
            "route": route, # 접근로 (경사로)
            "wheelchair": wheelchair, # 휠체어 대여
            "exit": exit, # 출입통로 (경사로)
            "elevator": elevator, # 엘리베이터
            "restroom": restroom, # 장애인 화장실
            "etc": detail.get("handicapetc"), # 기타상세
        }

    # 영유아 동반 그룹 필드 필터링
    elif type == "BABY":
        stroller = detail.get("stroller") # 유모차
        lactation = detail.get("lactationroom") # 수유실
        babychair = detail.get("babysparechair") # 유아의자

        # 부/적합 판단 기준
        # 수유실, 아기 의자가 없으면 부적합
        if is_blank(lactation) or is_blank(babychair):
            return {}

        return {
            "strolloer": stroller, # 유모차
            "lactation": lactation, # 수유실
            "babychair": babychair, # 유아의자
            "etc": detail.get("infantsfamilyetc"), # 기타상세
        }

    # 고령자 동반 그룹 필드 필터링 (평지/접근로 여부를 기준으로 함)
    elif type == "ELDERLY":
        route = detail.get("route")
        exit = detail.get("exit")
        elevator = detail.get("elevator")

        # 부/적합 판단 기준
        # 엘리베이터가 없으면 부적합
        if is_blank(elevator):
            return {}

        return {
            "route": route, # 접근로 (경사로)
            "exit": exit, # 출입통로 (경사로)
            "elevator": elevator,
            "etc": detail.get("handicapetc")
        }

    return {}

# 두 api 호출 후 결과를 비교해서 동반자 유형에 맞는 최종 후보 리스트 생성
def final_barrier_free_list(all_places: list, detail_places: list, type: str) -> dict:
    final_filtered = {"spots": [], "eats": [], "hotels": []}

    for item, detail in zip(all_places, detail_places):
        # 필터링 함수 호출
        filtered_places = filtered_partner_type(item, type)
        # print(filtered_places)

        # filtered_places가 비어있으면 부적합으로 간주 -> 후보에서 제외
        if not filtered_places:
            continue

        # areaBasedList2 호출 결과를 detailWithTour2에 던진 후 필터링한 결과 결합
        place_data = {
            "name": item.get("title"),
            "address": item.get("addr1"),
            "mapx": item.get("mapx"),
            "mapy": item.get("mapy"),
            "convenience_info": filtered_places
        }

        # contenttypeid 기준 최종 목록에 장소 유형을 분류해 후보 생성
        cnt_id = item.get("contenttypeid")

        # 12-관광지,, 14-문화시설, 15-행사/축제/공연, 38-쇼핑
        if cnt_id in ["12", "14", "15", "38"]:
            final_filtered["spots"].append(item)
        # 39-음식점
        elif cnt_id == "39":
            final_filtered["eats"].append(item)
        # 32-숙박
        elif cnt_id == "32":
            final_filtered["hotels"].append(item)

    return final_filtered