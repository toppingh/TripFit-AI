from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.request_controller import router as request_router

app = FastAPI(title="TripFit AI Server") # 서버 생성
app.include_router(request_router)

# URL
urls = [
    "http://localhost:3000", # 프론트 로컬 개발 주소
    "https://tripfit-web.vercel.app/", # 프론트 배포 주소
    "https://tripfit-backend-6que.onrender.com", # 백엔드 배포 주소
    "https://tripfit-ai.onrender.com/" # AI 배포 주소
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=urls,
    allow_credentials=True, # 로그인, 토큰, 쿠키 사용 (JWT)
    allow_methods=["*"], # HTTP 메서드 모두 허용
    allow_headers=["*"], # 모든 헤더 허용
)

@app.get("/")
def root():
    return {
        "status": "healty"
    }


