import asyncio
import json
import logging
import time
from datetime import timedelta
from google import genai
from google.genai import types

from app.config.settings import settings
from app.models.request_model import CourseResponse
from app.services import pet_service, barrier_free_filtering_service, tour_service, prompts

# debug 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tripfit.course_service")

client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def create_tripfit_course(city_code, state_code, type, start_date, end_date, total_days) -> dict:
    start_time = time.time() # 요청 시작 시간
    logger.info(f"[TripFit] 추천 코스 생성 요청 함수 호출 - 유형: {type}, 기간: {total_days}")

    # 1. 반려동물 동반 유형일 경우 (type == PET)
    if type == "PET":
        final_list = await pet_service.get_pet_list_and_filtered(city_code, state_code)

    # 2. 휠체어/고령자/영유아 동반 유형일 경우 (type == WHEELCHAIR, ELDERLY, BABY)
    else:
        places = await barrier_free_filtering_service.get_disability_list_and_filtered(city_code, state_code)
        all_places = places["spots"] + places["eats"] + places["hotels"]

        # 예외처리 - 1차 수집 실패
        if not all_places:
            logger.warning("1차 수집에 성공한 후보 장소가 없습니다. 요청을 중단합니다.")
            return {
                "error": "추천을 위한 공공 데이터 값이 부족합니다."
            }
        # debug 로그
        logger.info(f"[무장애] {len(all_places)}개 확보 완료 -> detailWithTour2 비동기 병렬 호출")
        api_start = time.time() # api호출 시간 체크

        # 1) 비동기 병럴 -> detailWithTour2를 호출해 동시에 여러 데이터 획득
        tasks = [tour_service.get_area_detail_info(item.get("contentid")) for item in all_places]
        detail_lists = await asyncio.gather(*tasks)

        # debug 로그
        logger.info(f"[무장애] detailWithTour2 비동기 호출 완료 - 소요 시간: {time.time() - api_start:.2f}초")

        final_list = barrier_free_filtering_service.final_barrier_free_list(all_places, detail_lists, type)

    # 예외처리 - 필터링 결과
    if not (final_list.get("spots") or final_list.get("eats") or final_list.get("hotels")):
        logger.warning("유형에 맞는 장소가 최종 필터링 결과에 없습니다. AI 호출을 중단합니다.")
        return {
            "error": "유형에 알맞은 무장애 장소가 없습니다."
        }

    # 3. 프롬프트 생성 (prompts.py 호출)
    # debug 로그
    logger.info("Gemini 프롬프트 호출")
    date_list = [start_date + timedelta(days=i) for i in range(total_days)]
    prompt = prompts.tripfit_prompt(type, total_days, date_list, final_list)

    # 4. Gemini Flash 연동
    # debug 로그
    logger.info("[Gemini] 프롬프트 전달 후 여행코스 생성 호출")
    gemini_start = time.time()

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CourseResponse,
            temperature=0.15
        )
    )

    # debug 로그
    logger.info(f"[Gemini] 응답 생성 완료 - 소요시간: {time.time() - gemini_start: .2f}초")
    total_time = time.time() - start_time
    logger.info(f"[TripFit] 추천 코스 생성 완료 - 총 소요시간: {total_time: .2f}초")

    return json.loads(response.text)