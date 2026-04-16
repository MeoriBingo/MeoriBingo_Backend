import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import text

# 각 기능별 라우터 임포트
from src.app.api import auth, users, mission, admin # admin.py를 가져옵니다.
from src.app.core.database import engine

load_dotenv()

# 전체 앱 설정 (단 한 번만 선언!)
app = FastAPI(title="Meori Bingo Project API")

# [라우터 등록 섹션]
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(mission.router, prefix="/api", tags=["Missions"])

# 질문자님이 만든 admin 기능을 연결합니다.
app.include_router(admin.router) 

@app.get("/")
def read_root():
    return {"message": "빙고 프로젝트 백엔드 서버가 정상 작동 중입니다."}

@app.get("/db-test")
def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {"status": "success", "message": "Azure DB 연결 성공!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")

