from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.models.user import User

# Swagger에서 사용할 토큰 URL 정의
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    현재 로그인한 유저를 가져오는 의존성 함수
    """
    # 1. 공통 예외 정의
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 자격 증명을 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # === [ 테스트 모드: 임시 ] ===
    # 주의: 개발 환경에서만 사용하세요.
    # 만약 토큰이 없거나 테스트가 우선이라면 특정 유저 반환
    # if not token:  # 토큰이 없을 때만 테스트 유저를 반환하고 싶다면 이 조건 추가
    test_user = db.query(User).filter(User.id == 6).first()
    if test_user:
        return test_user
    # ==========================

    # 2. 토큰 존재 여부 확인
    if not token:
        raise credentials_exception

    # 3. JWT 디코딩 및 검증
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError): # ValueError 추가 (id 변환 실패 대비)
        raise credentials_exception

    # 4. 데이터베이스 유저 조회
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user