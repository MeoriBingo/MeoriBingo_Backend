from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.models.user import User

# 토큰을 보낼 주소
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 자격 증명을 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 1. 토큰 복호화
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # 2. DB에서 실제 유저가 있는지 확인
    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise credentials_exception

    return user


# 실험용
