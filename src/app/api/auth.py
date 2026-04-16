from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import httpx

from src.app.core.config import settings
from src.app.core.security import create_access_token
from src.app.core.database import get_db
from src.app.models.user import User
from src.app.schemas.auth import LoginRequest, NicknameRequest  # 스키마에서 불러오기
from src.app.api.deps import get_current_user  # 토큰으로 현재 유저 가져오는 함수

router = APIRouter()


@router.post("/login")
async def kakao_login(request: LoginRequest, db: Session = Depends(get_db)):
    print(f"DEBUG: URL={settings.KAKAO_USER_INFO_URL}")
    print(f"DEBUG: Token={request.accessToken}")
    # 1. 카카오 서버 인증
    async with httpx.AsyncClient() as client:
        kakao_resp = await client.get(
            settings.KAKAO_USER_INFO_URL,
            headers={
                "Authorization": f"Bearer {request.accessToken}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8"},
            params={
            "client_id": settings.KAKAO_REST_API_KEY, # REST API 키
            "client_secret": settings.KAKAO_CLIENT_SECRET,
        }
        )

    if kakao_resp.status_code != 200:
        print(f"KAKAO ERROR: {kakao_resp.text}")
        raise HTTPException(status_code=401, detail="카카오 인증에 실패했습니다.")

    kakao_user = kakao_resp.json()
    kakao_id = str(kakao_user.get("id"))

    # 2. DB 조회 및 가입
    user = db.query(User).filter(User.social_id == kakao_id).first()

    if not user:
        user = User(social_id=kakao_id, nickname=None)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. 우리 서비스 전용 JWT 발급 (sub에 유저 ID 저장)
    my_token = create_access_token(data={"sub": str(user.id)})

    return {
        "status": "success",
        "message": "로그인 성공",
        "data": {
            "accessToken": my_token,
            "is_required_nickname": user.nickname is None,  # 닉네임 설정 필요 여부
            "user": {"id": user.id, "nickname": user.nickname},
        },
    }


@router.patch("/me/nickname")
async def update_nickname(
    request: NicknameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 닉네임 중복 체크
    existing_user = db.query(User).filter(User.nickname == request.nickname).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")

    current_user.nickname = request.nickname
    db.commit()
    return {"status": "success", "message": "닉네임 설정 완료"}
