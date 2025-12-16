# backend/main.py

from dotenv import load_dotenv
from fastapi import FastAPI

from backend.domains.registration.router import router as registration_router

# 환경변수 로드 (.env)
load_dotenv()

app = FastAPI()

# 회원가입/온보딩 라우터 등록
app.include_router(registration_router)


@app.get("/")
def root():
    return {"message": "ok"}
