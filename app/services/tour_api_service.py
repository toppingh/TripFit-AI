import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERVICE_KEY = os.getenv("API_SERVICE_DECODING_KEY")
BASE_URL = os.getenv("BASE_API_URL")

# 관광공사 API 호출

def get_area_places(areaCode: str):
    # 요청 주소
    url = f"{BASE_URL}/areaBasedList2"

    # 요청 파라미터
    params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "TripFit",
        "_type": "json",
        "areaCode": areaCode
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()
