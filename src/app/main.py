import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import text  # 추가됨
from app.api import auth 
from app.core.database import engine # database.py에서 만든 엔진을 가져오기

load_dotenv()

app = FastAPI()

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상 작동 중입니다."}

@app.get("/db-test")
def test_db_connection():
    try:

        with engine.connect() as connection:
    
            connection.execute(text("SELECT 1"))
            return {
                "status": "success",
                "message": "SQLAlchemy 엔진을 통한 Azure MySQL 연결 성공!"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")