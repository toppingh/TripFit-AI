import asyncio
import json
import logging
import re
import time
from datetime import timedelta

import httpx
from google import genai
from google.genai import types
from starlette.responses import StreamingResponse

from app.models.course_schema import FinalCourseResponse
from app.services import pet_service, barrier_free_filtering_service, tour_service, prompts
from app.services.congestion_service import get_congestion_rate

# 동반자 유형 맵핑
partner_mapping = {
    "PET": "반려동물",
    "WHEELCHAIR": "휠체어",
    "BABY": "영유아",
    "ELDERLY": "고령자"
}

# 서버에 로그 출력용 변수 생성
logger = logging.getLogger("tripfit.course_service")

# gemini client 변수 생성
client = genai.Client()

# 메인 함수 - 코스 생성
async def generate_tripfit_course(city_code, state_code, type, start_date, end_date, total_days):
    # 동반자 유형 한글로 변경
    kor_type = partner_mapping.get(type)

    # 1. 공공 데이터 수집 및 필터링
    print(f"[1단계] 공공 데이터 수집 및 필터링 진행 (동반 유형 : {type})")

    # 데이터 수집 시작 시간
    start_data_collect_time = time.perf_counter()

    # 동반자 유형 분기
    if type == "PET":
        final_list = await pet_service.get_pet_list_and_filtered(city_code, state_code)
    else:
        # 1차 - 지역 기반 목록 API 조회 (비동기)
        places = await barrier_free_filtering_service.get_disability_list_and_filtered(city_code, state_code)
        all_places = places['spots'] + places['eats'] + places['hotels']

        # 커넥션 풀 생성 - httpx.AsyncClient()
        async with httpx.AsyncClient() as http_client:
            # tour_service에 세션인 http_client, contentid 바인딩 -> task 목록 생성
            tasks = [
                tour_service.get_area_detail_info(http_client, item.get('contentid'))
                for item in all_places if item.get('contentid')
            ]
            # 생성한 단일 세션 -> 상세 조회 API 병렬 호출 (커넥션 풀)
            detail_lists = await asyncio.gather(*tasks)

        # 최종 결과 조합 + 필터링
        final_list = barrier_free_filtering_service.final_barrier_free_list(
            all_places, detail_lists, type, start_data_collect_time
        )

    date_list = [str(start_date + timedelta(days=i)) for i in range(total_days)]
    prompt = prompts.tripfit_prompt(type, total_days, date_list, final_list)

    # 데이터 수집 종료 시간
    end_data_collect_time = time.perf_counter()
    total_collect_time = end_data_collect_time - start_data_collect_time

    print(f"\n[1단계 완료] 소요 시간: {total_collect_time:.2f}초, 추출 후보 장소: {len(final_list)}개")

    # 2. Gemini 추론 -> 진입 시점에 스트리밍 제너레이터
    async def streaming_generator():
        # 클라이언트 연결 성공 후 추론 과정 출력
        logs = [
            f"한국관광공사 제공 데이터 중 {len(final_list)}개의 장소 수집 완료\n",
            f"수집한 장소에서 {kor_type} 동반 맞춤형 코스 분석 중\n",
            f"이동 동선 최적화 진행 중\n",
            f"최종 AI 추천 코스 생성 중\n"
        ]

        for log in logs:
            yield f"event: progress\ndata: {json.dumps({'message': log}, ensure_ascii=False)}\n\n"
            # yield log
            await asyncio.sleep(1.5)

        # gemini 호출 시간
        start_gemini = time.perf_counter()
        print(f"\n[2단계] Gemini 코스 생성 시작")

        # 스트림 응답 구조
        response = await client.aio.models.generate_content_stream(
            # model="gemini-3.1-flash-lite",
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FinalCourseResponse,
                temperature=0.15
            )
        )

        full_json_text = ""
        last_print_time = asyncio.get_event_loop().time()

        async for chunk in response:
            if chunk.text:
                full_json_text += chunk.text

            # 현재 작업 시간
            current_time = asyncio.get_event_loop().time()

            # AI 추론 장시간 소요될 경우 세션 끊김 방지 로그
            if current_time - last_print_time > 2.0:
                # yield "AI가 실시간 코스 세부 조율 중\n"
                f"event: progress\ndata: {json.dumps({'message': 'AI가 실시간 코스 세부 조율 중'}, ensure_ascii=False)}\n\n"
                last_print_time = current_time

        # gemini 작업 종료 시간
        end_gemini_time = time.perf_counter()
        # 총 gemini 작업 시간
        total_gemini_time = end_gemini_time - start_gemini

        print(f"\n[2단계 완료] Gemini 추론 총 소요 시간: {total_gemini_time:.2f}초")

        yield f"최종 추천 코스에서 관광지별 혼잡도 예측 중\n"

        try:
            match = re.search(r"(\{.*})", full_json_text, re.DOTALL)
            clean_json_text = match.group(1) if match else full_json_text.strip()

            # 최종 코스 결과
            course_result = json.loads(clean_json_text)

            # 혼잡도 예측 작업 시작 시간
            start_congestion_time = time.perf_counter()
            print(f"\n[3단계] 혼잡도 API 호출 시작")

            async with httpx.AsyncClient() as http_client:
                # api 응답 값 중 최종 코스 날짜와 맞는 혼잡도 필드 값 가져오기
                for idx, day in enumerate(course_result.get('days', [])):
                    visit_date = day.get('date') or day.get('visit_date')
                    if not visit_date and idx < len(date_list):
                        visit_date = date_list[idx]

                    day_tasks = []
                    places = day.get('places', [])

                    for place in places:
                        name = place.get('name')
                        task = get_congestion_rate(
                            client=http_client,
                            city_code=city_code,
                            state_code=state_code,
                            place_name=name,
                            visit_date=str(visit_date)
                        )
                        day_tasks.append(task)

                    # 혼잡도 예측 값 저장
                    congestion_results = await asyncio.gather(*day_tasks)

                    # 최종 코스에 관광지별 혼잡도 값 추가
                    for place, congestion in zip(places, congestion_results):
                        place['congestion'] = congestion

            # 혼잡도 예측 값 추가 작업 완료 시간
            end_congestion_time = time.perf_counter()

            # 3단계 총 작업 시간
            total_congestion_time = end_congestion_time - start_congestion_time

            # 최종 AI 추천 코스 생성 소요 시간
            total_time = end_congestion_time - start_data_collect_time

            print(f"\n[3단계 완료] 혼잡도 예측 소요 시간: {total_congestion_time:.2f}초")
            print(f"\n\n[AI 서버 작업 완료] 최종 AI 작업 시간: {total_time:.2f}초")

            # 최종 JSON 데이터에 구분선 추가
            yield "---\n"

            # JSON push
            yield json.dumps(course_result, ensure_ascii=False, indent=4)

        except Exception as e:
            logger.error(f"\n 최종 결과 값 가공 중 에러: {e}")
            # yield "혼잡도 예측 작업 중 에러가 발생해 AI 코스만 반환\n"
            # yield "---\n"
            # yield full_json_text

            f"event: progress\ndata: {json.dumps({'message': '최종 추천 코스에서 관광지별 혼잡도 예측 중'}, ensure_ascii=False)}\n\n"
            yield "event: done\n"
            yield f"data: {json.dumps(course_result, ensure_ascii=False)}\n\n"


    # 클라이언트와 SSE 커넥션
    return StreamingResponse(
        streaming_generator(),
        media_type='text/event-stream',
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Content-Type": "text/event-stream",
        }
    )