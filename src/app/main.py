import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import text

# 1. 모든 라우터들을 파일 상단에서 한 번에 임포트합니다.
from src.app.api import auth, users, mission, social, bingo, bingo_detail, admin
from src.app.core.database import engine

load_dotenv()

# 2. 전체 앱 설정 (단 한 번만 선언!)
app = FastAPI(title="Meori Bingo Project API")

# 3. 라우터 등록 섹션 (누락되거나 중복된 것 없이 정리했습니다)
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(mission.router, prefix="/api", tags=["Missions"])

# 질문자님의 관리자(Admin) 기능을 연결합니다.
app.include_router(admin.router) 

# 팀원들의 추가 기능을 연결합니다.
app.include_router(social.router, prefix="/api/social", tags=["Social"])
app.include_router(bingo.router, prefix="/api", tags=["Bingo"])
app.include_router(bingo_detail.router, prefix="/api/bingo", tags=["Bingo Detail"])

# 4. 기본 경로 및 DB 테스트
@app.get("/")
def read_root():
    return {"message": "빙고 프로젝트 백엔드 서버가 정상 작동 중입니다."}

@app.get("/db-test")
def test_db_connection():
    """SQLAlchemy 엔진을 사용해 Azure MySQL 연결을 확인합니다."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return {
                "status": "success",
                "message": "Azure DB 연결 성공!",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")

