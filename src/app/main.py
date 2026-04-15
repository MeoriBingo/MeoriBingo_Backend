import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
<<<<<<< HEAD
from sqlalchemy import text  # 추가됨
from app.api import auth 
from app.core.database import engine # database.py에서 만든 엔진을 가져오기
=======
from sqlalchemy import text 

# 최신 인증(카카오) 라우터와 데이터베이스 엔진 임포트
from app.api import auth 
from app.core.database import engine 
>>>>>>> 868c814

load_dotenv()

app = FastAPI()

<<<<<<< HEAD
=======
# 1. 라우터 등록: 카카오 로그인 및 닉네임 설정 관련 API 연결
# 기존 user_router 대신 새로운 auth.router를 사용합니다.
>>>>>>> 868c814
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상 작동 중입니다."}

@app.get("/db-test")
def test_db_connection():
    """
    SQLAlchemy 엔진을 사용해 Azure MySQL 연결을 확인합니다.
    """
    try:
<<<<<<< HEAD

        with engine.connect() as connection:
    
=======
        # database.py에서 설정한 engine을 사용하여 연결 테스트
        with engine.connect() as connection:
>>>>>>> 868c814
            connection.execute(text("SELECT 1"))
            return {
                "status": "success",
                "message": "SQLAlchemy 엔진을 통한 Azure MySQL 연결 성공!"
            }
    except Exception as e:
<<<<<<< HEAD
=======
        # 연결 실패 시 상세 에러를 반환하여 디버깅을 돕습니다.
>>>>>>> 868c814
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")