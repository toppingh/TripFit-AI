# 관광공사 API 호출

def get_tour_place(region_code: str):
    if region_code == "J0":
        return [
            {
                "name": "성산일출봉",
                "description": "제주의 대표 관광지",
                "wheelChair": True
            },{
                "name": "고기국수",
                "description": "제주의 대표 맛집이자 웨이팅이 항상 즐비한 인기 식당",
                "wheelChair": True
            },
        ]
    return []