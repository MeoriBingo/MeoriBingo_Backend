from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import httpx

from src.app.core.config import settings
from src.app.core.security import create_access_token
from src.app.core.database import get_db
from src.app.models.user import User
from src.app.schemas.auth import LoginRequest, NicknameRequest
from src.app.api.deps import get_current_user

router = APIRouter()


@router.post("/login")
async def kakao_login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    카카오톡을 이용한 로그인 프로세스를 진행합니다.
    """
    # 1. 인가 코드로 카카오 토큰 발급 요청 (POST 방식)
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_REST_API_KEY,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "code": request.authorizationCode,
        "client_secret": settings.KAKAO_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        # 이 부분이 바로 POST인데 Body(data)를 실어 보내는 부분입니다!
        token_resp = await client.post(token_url, data=token_data)

        if token_resp.status_code != 200:
            print(f"TOKEN ERROR: {token_resp.text}")
            raise HTTPException(
                status_code=401, detail="카카오 토큰 발급에 실패했습니다."
            )

        kakao_tokens = token_resp.json()
        real_access_token = kakao_tokens.get("access_token")

        # 2. 받은 진짜 access_token으로 사용자 정보 가져오기
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {real_access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }

        user_resp = await client.post(user_info_url, headers=headers)

    if user_resp.status_code != 200:
        print(f"USER INFO ERROR: {user_resp.text}")
        raise HTTPException(
            status_code=401, detail="카카오 사용자 정보 조회에 실패했습니다."
        )

    kakao_user = user_resp.json()
    kakao_id = str(kakao_user.get("id"))

    # 3. DB 조회 및 회원가입 로직
    user = db.query(User).filter(User.social_id == kakao_id).first()

    if not user:
        temp_nickname = f"BINGO_{kakao_id[:5]}"
        user = User(social_id=kakao_id, social_provider="KAKAO", nickname=temp_nickname)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4. 우리 서비스 전용 JWT 발급
    my_token = create_access_token(data={"sub": str(user.id)})

    is_required_nickname = user.nickname.startswith("BINGO_")

    return {
        "status": "success",
        "message": "로그인 성공",
        "data": {
            "accessToken": my_token,
            "is_required_nickname": is_required_nickname,
            "user": {"id": user.id, "nickname": user.nickname},
        },
    }


# 닉네임 업데이트 API
@router.patch("/me/nickname")
async def update_nickname(
    request: NicknameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    사용자의 닉네임을 변경합니다.
    """
    existing_user = db.query(User).filter(User.nickname == request.nickname).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")

    current_user.nickname = request.nickname
    db.commit()
    return {"status": "success", "message": "닉네임 설정 완료"}
