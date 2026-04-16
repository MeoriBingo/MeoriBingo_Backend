from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from sqlalchemy import or_, and_
from src.app.core.database import get_db
from src.app.models.social import Friendship
from src.app.schemas.social import (
    FriendshipCreate,
    FriendshipRead,
    FriendshipUpdate,
    FriendRequestRead,
    FriendBingoStatus,
    FriendListResponse,
)
from src.app.api import deps
from src.app.models.user import User
from src.app.models.bingo import BingoBoard


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
    requests = (
        db.query(Friendship)
        .filter(Friendship.addressee_id == my_user_id, Friendship.status == "PENDING")
        .all()
    )

    return requests


@router.get("/friends/bingo", response_model=List[FriendBingoStatus])
async def get_friends_bingo_status(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)
):
    # 1. 친구 목록 조회 (내가 요청했거나, 요청받았거나 둘 다 포함)
    friends_query = (
        db.query(Friendship)
        .filter(
            and_(
                or_(
                    Friendship.requester_id == current_user.id,
                    Friendship.addressee_id == current_user.id,
                ),
                Friendship.status == "ACCEPTED",
            )
        )
        .all()
    )

    friend_ids = []
    for f in friends_query:
        if f.requester_id == current_user.id:
            friend_ids.append(f.addressee_id)
        else:
            friend_ids.append(f.requester_id)

    if not friend_ids:
        return []

    # 2. 친구들의 정보와 빙고 현황 조회
    # (참고: 실제 비즈니스 로직에 따라 Bingo 테이블과의 Join이 필요합니다)
    results = []
    for f_id in friend_ids:
        friend = db.query(User).filter(User.id == f_id).first()
        # 해당 친구의 가장 최근 빙고판 정보를 가져온다고 가정
        bingo = (
            db.query(BingoBoard)
            .filter(BingoBoard.user_id == f_id)
            .order_by(BingoBoard.created_at.desc())
            .first()
        )

        if friend:
            results.append(
                {
                    "user_id": friend.id,
                    "nickname": friend.nickname,
                    "profile_image": friend.profile_image,
                    "bingo_count": bingo.completed_lines if bingo else 0,
                    "progress_percentage": (
                        (bingo.marked_cells / 25 * 100) if bingo else 0
                    ),
                    "last_updated": bingo.updated_at if bingo else friend.created_at,
                }
            )
    return results


@router.get("/friends/me", response_model=FriendListResponse)
def get_friend_list(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)
):
    """
    내 친구 목록을 조회합니다.
    """
    # STEP 1: ACCEPTED 친구 관계 조회
    friendships = (
        db.query(Friendship)
        .filter(
            and_(
                or_(
                    Friendship.requester_id == current_user.id,
                    Friendship.addressee_id == current_user.id,
                ),
                Friendship.status == "ACCEPTED",
            )
        )
        .all()
    )

    # STEP 2: 상대방 ID 추출
    friend_ids = []
    for fs in friendships:
        if fs.requester_id == current_user.id:
            friend_ids.append(fs.addressee_id)
        else:
            friend_ids.append(fs.requester_id)

    # STEP 3: 친구가 없으면 빈 배열 반환
    if not friend_ids:
        return {
            "status": "success",
            "message": "요청이 성공적으로 처리되었습니다.",
            "data": [],
        }

    # STEP 4: 친구들 정보 가져오기
    friends = db.query(User).filter(User.id.in_(friend_ids)).all()

    return {
        "status": "success",
        "message": "요청이 성공적으로 처리되었습니다.",
        "data": friends,
    }
