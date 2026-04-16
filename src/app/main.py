import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import text

# 최신 인증(카카오) 라우터와 데이터베이스 엔진 임포트
from src.app.api import admin
from src.app.api import auth
from src.app.core.database import engine
from src.app.api import users
from src.app.api import mission

load_dotenv()

app = FastAPI()

# 1. 라우터 등록: 카카오 로그인 및 닉네임 설정 관련 API 연결
# 기존 user_router 대신 새로운 auth.router를 사용합니다.
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api")
app.include_router(mission.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상 작동 중입니다."}


@app.get("/db-test")
def test_db_connection():
    """
    SQLAlchemy 엔진을 사용해 Azure MySQL 연결을 확인합니다.
    """
    try:
        # database.py에서 설정한 engine을 사용하여 연결 테스트
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {
                "status": "success",
                "message": "SQLAlchemy 엔진을 통한 Azure MySQL 연결 성공!",
            }
    except Exception as e:
        # 연결 실패 시 상세 에러를 반환하여 디버깅을 돕습니다.
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")



###### adimin 연결 ######

from fastapi import FastAPI
from app.api.admin import admin # 파일 임포트

app = FastAPI()

# 작성하신 파일들을 등록합니다.
app.include_router(admin.router)



