from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.app.core.database import get_db
from src.app.models.social import Friendship  # 우리가 찾은 모델!
from src.app.schemas.social import FriendRequestRead # 방금 만든 접시!

router = APIRouter()

@router.get("/friends/requests", response_model=List[FriendRequestRead])
def get_friend_requests(db: Session = Depends(get_db)):
    """
    나에게 온 친구 신청 목록을 조회합니다.
    """
    # ⚠️ 임시로 내 유저 ID를 1번이라고 가정해볼게요! 
    # (나중에 고수님들이 알려주실 '현재 로그인 유저 정보'로 바꿀 부분입니다)
    my_user_id = 1 

    # 1. 창고(DB)에서 조건에 맞는 데이터 긁어오기
    # 받는 사람이 '나'이고, 상태가 'PENDING'인 것들만!
    requests = db.query(Friendship).filter(
        Friendship.addressee_id == my_user_id,
        Friendship.status == "PENDING"
    ).all()

    return requests