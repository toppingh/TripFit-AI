import asyncio
import json
from datetime import timedelta
from google import genai
from google.genai import types

from app.config.settings import settings
from app.models.request_model import CourseResponse
from app.services import pet_service, barrier_free_filtering_service, tour_service, prompts

client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def create_tripfit_course(city_code, state_code, type, start_date, end_date, total_days) -> dict:
    # 1. 반려동물 동반 유형일 경우 (type == PET)
    if type == "PET":
        final_list = await pet_service.get_pet_list_and_filtered(city_code, state_code)

    # 2. 휠체어/고령자/영유아 동반 유형일 경우 (type == WHEELCHAIR, ELDERLY, BABY)
    else:
        places = await barrier_free_filtering_service.get_disability_list_and_filtered(city_code, state_code)
        all_places = places["spots"] + places["eats"] + places["hotels"]

        # 1) 비동기 병럴 -> detailWithTour2를 호출해 동시에 여러 데이터 획득
        tasks = [tour_service.get_area_detail_info(item.get("contentid")) for item in all_places]
        detail_lists = await asyncio.gather(*tasks)

        final_list = barrier_free_filtering_service.final_barrier_free_list(all_places, detail_lists, type)

    # 3. 프롬프트 생성 (prompts.py 호출)
    date_list = [start_date + timedelta(days=i) for i in range(total_days)]
    prompt = prompts.tripfit_prompt(type, total_days, date_list, final_list)

    # 4. Gemini Flash 연동
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CourseResponse,
            temperature=0.7

        )
    )

    return json.loads(response.text)