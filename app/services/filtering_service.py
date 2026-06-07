def get_place_data(data):

    items = (
        data["response"]
        ["body"]
        ["items"]
        ["item"]
    )

    # 응답 값 중 필요 데이터만 추출하여 저장
    places = []

    for item in items:
        places.append({
            "name": item.get("title"),
            "contentId": item.get("contentid"),
            # 관광타입 (12-관광지, 14-문화시설, 15-행사/공연/축제, 28-레포츠, 32-숙박, 38-쇼핑, 39-음식점)
            "contentTypeId": str(
                item.get("contenttypeid")
            ),
            "lon": item.get("mapx"), # 경도
            "lat": item.get("mapy"), # 위도
            "addr": item.get("addr1"),
            "img": item.get("firstimage2") # 썸네일
        })

    return places

# 관광지, 식당 필터링
def filtering_places(places):

    # 관광지 분리
    tour_spots = [
        t
        for t in places
        if t["contentTypeId"] == "12"
    ]

    # 식당 분리
    eat_spots = [
        e
        for e in places
        if e["contentTypeId"] == "39"
    ]

    # 숙박 분리
    hotel_spots = [
        h
        for h in places
        if h["contentTypeId"] == "32"
    ]

    # 축제 분리
    festival_spots = [
        f
        for f in places
        if f["contentTypeId"] == "15"
    ]

    return {
        "tours": tour_spots,
        "eats": eat_spots,
        "hotels": hotel_spots,
        "festivals": festival_spots
    }