import logging
import time
import json

from app.services.req_api_service import req_area_list_api

# debug 로그
logger = logging.getLogger("tripfit.barrier_free_service")

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

async def get_disability_list_and_filtered(city_code, state_code):
    logger.info(f"[무장애] 1차 지역기반 APi 호출 - city: {city_code}, state: {state_code}")

    # 파라미터 설정
    params = {
        "lDongRegnCd": city_code
    }

    # 시군구 값 확인 후 파라미터 추가
    if state_code and str(state_code).strip():
        params["lDongSignguCd"] = state_code

    # params 전달
    data = await req_area_list_api(
        "KorWithService2/areaBasedList2",
        params
    )
    logger.info(f"[무장애] 1차 API 원본 데이터 수집 결과 - 총 {len(data) if data else 0}건")

    filtered = {"spots": [], "eats": [], "hotels": []}
    if not data:
        return filtered

    for item in data:
        cnt_id = item.get("contenttypeid")

        if cnt_id in ["12", "14", "15", "38"]:
            filtered["spots"].append(item)
        elif cnt_id == "39":
            filtered["eats"].append(item)
        elif cnt_id == "32":
            filtered["hotels"].append(item)

    logger.info(f"[무장애] 1차 분류 결과 - 관광지: {len(filtered['spots'])}건, 식당: {len(filtered['eats'])}건, 숙박: {len(filtered['hotels'])}건")
    log_category_details("관광지", filtered["spots"])
    log_category_details("식당", filtered["eats"])
    log_category_details("숙박", filtered["hotels"])

    return filtered


def extract_detail_item(detail_response):
    if not detail_response:
        return {}
    try:
        # API 응답 구조 -> response.body.items.item
        response_obj = detail_response.get("response", {})
        body_obj = response_obj.get("body", {})
        items_obj = body_obj.get("items", {})
        item_list = items_obj.get("item", [])

        if item_list and isinstance(item_list, list):
            return item_list[0]
        elif isinstance(item_list, dict):
            return item_list
    except Exception:
        pass
    return detail_response


def filtered_partner_type(detail_raw, type):
    detail = extract_detail_item(detail_raw)
    if not detail:
        return {}

    # 값이 존재하는 필드만 append
    res = {}

    # 둥반자 유형 == 휠체어
    if type == "WHEELCHAIR":
        if detail.get("parking"): res["parking"] = detail["parking"]

        # 대소문자 변동성 방어 (publictransport / publicTransport)
        pt = detail.get("publictransport") or detail.get("publicTransport")
        if pt: res["publicTransport"] = pt

        # 휠체어 동반 시 참고할 필드 값 (route, wheelchair, exit, elevator, restroom, handicapetc)
        if detail.get("route"): res["route"] = detail["route"] # 경사/접근로
        if detail.get("wheelchair"): res["wheelchair"] = detail["wheelchair"] # 휠체어 대여
        if detail.get("exit"): res["exit"] = detail["exit"] # 출입구
        if detail.get("elevator"): res["elevator"] = detail["elevator"] # 엘리베이터 유무
        if detail.get("restroom"): res["restroom"] = detail["restroom"] # 장애인 화장실 유무
        if detail.get("handicapetc"): res["etc"] = detail["handicapetc"] # 기타상세

    # 동반자 유형 == 영유아
    elif type == "BABY":

        # 영유아 동반 시 참고할 필드 값 (stroller, lactationroom, babysparechair, infantsfamilyetc)
        if detail.get("stroller"): res["stroller"] = detail["stroller"] # 유모차 대여 유무
        if detail.get("lactationroom"): res["lactation"] = detail["lactationroom"] # 수유실 유무
        if detail.get("babysparechair"): res["babychair"] = detail["babysparechair"] # 아기의자 유무
        if detail.get("infantsfamilyetc"): res["etc"] = detail["infantsfamilyetc"] # 기타상세

    # 동반자 유형 == 고령자
    elif type == "ELDERLY":

        # 고령자 동반 시 참고할 필드 값 (route, exit, elevator, handicapetc)
        if detail.get("route"): res["route"] = detail["route"] # 경사/접근로
        if detail.get("exit"): res["exit"] = detail["exit"] # 출입구
        if detail.get("elevator"): res["elevator"] = detail["elevator"] # 엘리베이터 유무
        if detail.get("handicapetc"): res["etc"] = detail["handicapetc"] # 기타상세

    return res


# 무장애 여행 최종 목록
def final_barrier_free_list(all_places, detail_places, type, start_time):
    logger.info(f"[무장애] {type} 동반 맞춤형 코스 필터링 시작")

    # 필터링 변수 (관광지, 식당, 숙소)
    final_filtered = {"spots": [], "eats": [], "hotels": []}

    for item, detail in zip(all_places, detail_places):
        filtered_places = filtered_partner_type(detail, type)

        # 응답 데이터가 비어있는 경우 제외
        if not filtered_places:
            continue

        place_data = {
            "name": item.get("title"),
            "address": item.get("addr1"),
            "mapx": item.get("mapx"),
            "mapy": item.get("mapy"),
            "convenience_info": filtered_places, # 위에서 동반자 유형 별 참고할 필드 값 정리한 변수
            "img": item.get("firstimage", ""),
            "contenttypeid": item.get("contenttypeid")
        }

        cnt_id = item.get("contenttypeid")

        if cnt_id in ["12", "14", "15", "38"]: # 12-관광지, 14-문화시설, 15-행사/축제/공연, 38-쇼핑
            final_filtered["spots"].append(place_data)
        elif cnt_id == "39": # 39-음식점
            final_filtered["eats"].append(place_data)
        elif cnt_id == "32": # 32-숙박
            final_filtered["hotels"].append(place_data)

    elapsed_time_str = "시간 측정 불가 -> start_time 누락"
    if start_time:
        elapsed_time = time.perf_counter() - start_time
        # 최종 작업 소요 시간
        elapsed_time_str = f"{elapsed_time:.2f}초"


    # 테스트 디버그용
    debug_payload = {
        "CHECK_POINT": "[1단계] 공공 API 데이터 수집 및 무장애 필터링 완료",
        "ELAPSED_TIME": elapsed_time_str,
        "total_spots_count": len(final_filtered["spots"]),
        "total_eats_count": len(final_filtered["eats"]),
        "total_hotels_count": len(final_filtered["hotels"]),
        "final_filtered_data": final_filtered
    }

    # gemini 호출 전 debug용 강제 에러 출력
    # raise ValueError(json.dumps(debug_payload, ensure_ascii=False))

    return final_filtered