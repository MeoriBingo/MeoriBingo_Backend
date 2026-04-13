import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

load_dotenv()

# 접속 정보 설정
config = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "ssl_ca": os.getenv("SSL_CA"),
    "ssl_disabled": False,  # 인증서 사용
}

try:
    # 연결 시도
    print("Azure MySQL에 연결 중...")
    cnx = mysql.connector.connect(**config)

    if cnx.is_connected():
        print("✅ 연결 성공!")

        # 3. 간단한 쿼리 실행 (서버 버전 확인)
        cursor = cnx.cursor()
        cursor.execute("SELECT VERSION();")
        row = cursor.fetchone()
        print(f"서버 버전: {row[0]}")

        cursor.close()

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("❌ 사용자명 또는 비밀번호가 틀렸습니다.")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("❌ 데이터베이스가 존재하지 않습니다.")
    else:
        print(f"❌ 에러 발생: {err}")
else:
    cnx.close()
    print("연결이 안전하게 종료되었습니다.")
