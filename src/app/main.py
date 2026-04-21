import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# API 라우터 임포트 (중복 제거 및 정리)
from src.app.api import auth, users, mission, social, bingo, bingo_detail, admin
from src.app.core.database import engine

load_dotenv()

app = FastAPI(title="MeoriBingo API")

# CORS 설정 (프론트엔드와 연결을 위해 필요할 수 있습니다)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포시에는 특정 도메인만 허용하도록 수정 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 섹션 (경로와 태그를 일관성 있게 정리했습니다)
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(mission.router, prefix="/api/mission", tags=["Mission"])
app.include_router(social.router, prefix="/api/social", tags=["Social"])
app.include_router(bingo.router, prefix="/api/bingo", tags=["Bingo"])
app.include_router(bingo_detail.router, prefix="/api/bingo-detail", tags=["Bingo Detail"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
def read_root():
    return {"message": "빙고 프로젝트 백엔드 서버가 정상 작동 중입니다."}

@app.get("/db-test")
def test_db_connection():
    """SQLAlchemy 엔진을 사용해 DB 연결을 확인합니다."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {
                "status": "success",
                "message": "DB 연결 성공!",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")