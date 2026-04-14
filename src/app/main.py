import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import mysql.connector
from mysql.connector import Error

load_dotenv()

app = FastAPI()

# DB 설정 정보
SSL_CA = os.getenv("SSL_CA")
if SSL_CA and not os.path.isabs(SSL_CA):
    SSL_CA = os.path.join(os.getcwd(), SSL_CA)

db_config = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "ssl_ca": SSL_CA,
    "ssl_disabled": False,  # 인증서 사용
}


@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상 작동 중입니다."}


@app.get("/db-test")
def test_db_connection():
    try:
        # DB 연결 시도
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            # 서버 정보 가져오기
            db_info = connection.get_server_info()
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()

            connection.close()  # 연결 닫기

            return {
                "status": "success",
                "message": "Azure MySQL 연결 성공!",
                "server_version": db_info,
                "current_database": record[0],
            }

    except Error as e:
        # 연결 실패 시 500 에러 반환
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")
