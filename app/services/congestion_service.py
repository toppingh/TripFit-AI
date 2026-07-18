import httpx
import logging
import re  # 날짜 포맷 정제
from app.config.settings import settings

logger = logging.getLogger("tripfit.congestion_service")


async def get_congestion_rate(
        client: httpx.AsyncClient,
        city_code: str,
        state_code: str,
        place_name: str,
        visit_date: str  # 해당 관광지 방문 날짜 (start_date)
) -> str:
    endpoint = f"{settings.BASE_URL}/TatsCnctrRateService/tatsCnctrRatedList"

    # 혼잡도 API에서 시군구 코드 아래와 같이 가공 필요 (시도코드+시군구코드)
    combined_signgu_code = f"{city_code}{state_code}"

    # visit_date에 포함된 -, / 제거 -> "20260713"
    target_date = re.sub(r"[^0-9]", "", str(visit_date))

    params = {
        "serviceKey": settings.TOUR_API_KEY,
        "MobileOS": settings.MOBILE_OS,
        "MobileApp": settings.MOBILE_APP,
        "_type": settings.TYPE,
        "areaCd": city_code,  # 시도 코드
        "signguCd": combined_signgu_code,  # 시도+시군구 결합 코드
        "tAtsNm": place_name,
        # "pageNo": 1,
        # "numOfRows": 30
    }

    # print(f"\n[혼잡도 날짜 매칭 API 요청]")
    # print(f"요청 장소: {place_name} | 목표 방문일: {target_date}")
    # print(f"시도코드: {city_code} | 시군구코드: {combined_signgu_code}")

    try:
        response = await client.get(endpoint, params=params, timeout=5.0)

        if response.status_code == 200:
            data = response.json()

            body = data.get("response", {}).get("body", {})
            items_dict = body.get("items")

            item_list = []
            if isinstance(items_dict, dict):
                item_list = items_dict.get("item", [])

            if item_list:
                # 응답 데이터 중 target_date와 일치하는 날짜 찾기
                matched_item = None
                for item in item_list:
                    if item.get("baseYmd") == target_date:
                        matched_item = item
                        break

                # 1. 원하는 날짜의 데이터가 매칭된 경우
                if matched_item:
                    congestion_rate = matched_item.get("cnctrRate")
                    # print(f"날짜 매칭 성공. {target_date} -> {congestion_rate}%")
                    return f"{congestion_rate}%"

                # 2. API 응답 값은 있으나 해당 날짜만 없는 경우 (30일 이후 여행 시작일일 경우)
                else:
                    # 백업 - 첫 번째(가장 가까운 날짜) 데이터 반환
                    fallback_rate = item_list[0].get("cnctrRate")
                    fallback_date = item_list[0].get("baseYmd")
                    return f"{fallback_rate}%"
            else:
                print(f"[{place_name}] 데이터 매칭 실패: 응답 리스트가 비어있습니다.")

        else:
            print(f"[API 서버 에러] - (HTTP {response.status_code})")

        return "정보 없음"

    except httpx.TimeoutException:
        print(f"[{place_name}] 혼잡도 API 타임아웃")
        return "정보 없음"
    except Exception as e:
        print(f"[{place_name}] 예외 발생: {e}")
        return "정보 없음"