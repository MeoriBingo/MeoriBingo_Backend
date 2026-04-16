from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.app.core.database import get_db
from src.app.models.social import Friendship
from src.app.models.user import User
from src.app.schemas.social import FriendRequestRead
from src.app.api.deps import get_current_user

router = APIRouter()

@router.get("/friends/requests", response_model=List[FriendRequestRead])
def get_friend_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    """
    나에게 온 친구 신청 목록을 조회합니다.
    """
    # 내 ID가 addressee_id로 되어 있는 신청들 전부 찾아드려
    requests = (
        db.query(Friendship)
        .filter(
            Friendship.addressee_id == current_user.id,
            Friendship.status == "PENDING"
        )
        .all()
    )

    # 닉네임 합쳐서 리스트에 담아드려
    result = []
    for req in requests:
        sender = db.query(User).filter(User.id == req.requester_id).first()

        result.append({
            "id": req.id,
            "requester_id": req.requester_id,
            "requester_nickname": sender.nickname if sender else "알 수 없음",
            "status": req.status,
            "created_at": req.created_at
        })

    return requests