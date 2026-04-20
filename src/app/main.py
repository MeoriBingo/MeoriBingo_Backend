import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# 1. social 임포트 추가
from src.app.api import auth, users, mission, social, bingo, admin, bingo_detail
from src.app.core.database import engine

load_dotenv()

app = FastAPI()


# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS 등 모든 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 2. 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(mission.router, prefix="/api/mission", tags=["Mission"])
app.include_router(social.router, prefix="/api/social", tags=["Social"])
app.include_router(bingo.router, prefix="/api/bingo", tags=["Bingo"])
app.include_router(bingo_detail.router, prefix="/api/history", tags=["Bingo Details"])
app.include_router(admin.router, prefix="/api/admin/point", tags=["Admin"])
app.include_router(bingo.router, prefix="/api/bingo", tags=["Bingo Management"])


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
