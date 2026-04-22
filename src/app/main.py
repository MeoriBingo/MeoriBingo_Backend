import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.app.api import auth, users, mission, bingo, admin, bingo_detail, friends, reactions 
from src.app.core.database import engine

load_dotenv()

app = FastAPI(title="Bingo Project API") 

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 라우터 등록 (중복 제거 및 경로 정리)
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(mission.router, prefix="/api/mission", tags=["Mission"])

# 소셜(친구/리액션) 라우터: prefix를 /api/social로 설정
app.include_router(friends.router, prefix="/api/social", tags=["Friends"])
app.include_router(reactions.router, prefix="/api/social/reactions", tags=["Reactions"])

app.include_router(bingo.router, prefix="/api/bingo", tags=["Bingo"])
app.include_router(bingo_detail.router, prefix="/api/history", tags=["Bingo Details"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상 작동 중입니다."}

@app.get("/db-test")
def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {"status": "success", "message": "DB 연결 성공!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")