from fastapi import FastAPI
from app.routes.recommend import router

app = FastAPI()
app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "TripFit AI Server"
    }