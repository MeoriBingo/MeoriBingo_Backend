import os
from dotenv import load_dotenv

# .env 파일을 읽어옵니다.
load_dotenv()

class Settings:
    PROJECT_NAME: str = "MeoriBingo"
    
    # 카카오 설정
    KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
    KAKAO_USER_INFO_URL = os.getenv("KAKAO_USER_INFO_URL")
    
    # JWT 보안 설정
    JWT_SECRET = os.getenv("JWT_SECRET")
    ALGORITHM = os.getenv("ALGORITHM", "HS256") # 값이 없으면 기본값 HS256 사용
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

settings = Settings()