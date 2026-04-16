from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.app.core.database import get_db
from src.app.models.social import Friendship
from src.app.models.user import User
from src.app.schemas.social import FriendshipCreate, FriendshipRead, FriendshipUpdate

router = APIRouter(prefix="/social", tags=["Social"])


@router.patch("/friends/requests/{friendship_id}", response_model=FriendshipRead)
async def update_friend_request(
    friendship_id: int,
    friendship_update: FriendshipUpdate,
    db: Session = Depends(get_db),
):
    """
    친구 신청을 수락하거나 거절합니다.
    - friendship_id: 친구 신청 관계의 고유 ID
    - user_id: 수락/거절 액션을 취하는 유저의 ID (addressee_id와 일치해야 함)
    - status: 'ACCEPTED' 또는 'REJECTED'
    """
    # 친구 신청 내역 조회
    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="친구 신청 내역을 찾을 수 없습니다.",
        )

    # 신청받은 사람(addressee_id)이 요청을 처리하는지 확인
    if friendship.addressee_id != friendship_update.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인에게 온 친구 신청만 수락하거나 거절할 수 있습니다.",
        )

    # 현재 상태가 'PENDING'인지 확인
    if friendship.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 처리된 친구 신청입니다.",
        )

    # 상태 업데이트 (ACCEPTED 또는 REJECTED)
    if friendship_update.status not in ["ACCEPTED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="상태는 'ACCEPTED' 또는 'REJECTED'여야 합니다.",
        )

    friendship.status = friendship_update.status
    db.commit()
    db.refresh(friendship)

    return friendship


@router.post(
    "/friends/request",
    response_model=FriendshipRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_friend_request(
    friendship_in: FriendshipCreate, db: Session = Depends(get_db)
):
    """
    친구 신청을 생성합니다.
    - requester_id: 신청한 사람의 user_id
    - addressee_id: 신청받은 사람의 user_id
    - status: 기본 'PENDING'
    """
    # 자기 자신에게 신청하는지 확인
    if friendship_in.requester_id == friendship_in.addressee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신에게 친구 신청을 보낼 수 없습니다.",
        )

    # 양쪽 사용자 존재 여부 확인
    requester = db.query(User).filter(User.id == friendship_in.requester_id).first()
    addressee = db.query(User).filter(User.id == friendship_in.addressee_id).first()
    if not requester or not addressee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다."
        )

    # 이미 친구 관계이거나 신청 중인지 확인 (중복 방지)
    existing_friendship = (
        db.query(Friendship)
        .filter(
            or_(
                (Friendship.requester_id == friendship_in.requester_id)
                & (Friendship.addressee_id == friendship_in.addressee_id),
                (Friendship.requester_id == friendship_in.addressee_id)
                & (Friendship.addressee_id == friendship_in.requester_id),
            )
        )
        .first()
    )

    if existing_friendship:
        if existing_friendship.status == "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 대기 중인 친구 신청이 있습니다.",
            )
        elif existing_friendship.status == "ACCEPTED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="이미 친구 상태입니다."
            )

    # 새로운 친구 신청 생성
    new_friendship = Friendship(
        requester_id=friendship_in.requester_id,
        addressee_id=friendship_in.addressee_id,
        status="PENDING",
    )

    db.add(new_friendship)
    db.commit()
    db.refresh(new_friendship)

    return new_friendship
