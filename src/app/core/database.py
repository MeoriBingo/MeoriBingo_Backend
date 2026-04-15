import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# .env 파일 로드
load_dotenv()

# DB 접속 정보
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
SSL_CA = os.getenv("SSL_CA")

# Azure MySQL 연결 URL (특수문자 포함 비밀번호를 위해 quote_plus 사용)
encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
)

# SSL 설정 (인증서가 있는 경우에만)
connect_args = {}
if SSL_CA:
    # 절대 경로인지 확인하거나, 현재 디렉토리 기준 경로 확인
    if not os.path.isabs(SSL_CA):
        current_dir = os.getcwd()
        SSL_CA_PATH = os.path.join(current_dir, SSL_CA)
    else:
        SSL_CA_PATH = SSL_CA

    if os.path.exists(SSL_CA_PATH):
        connect_args["ssl"] = {"ca": SSL_CA_PATH}

# DB 엔진 생성
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 나중에 API 만들 때 사용함
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
