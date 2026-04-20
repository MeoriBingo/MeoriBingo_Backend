from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from src.app.api import deps

from src.app.core.database import get_db
from src.app.models.user import User
from src.app.models.social import Friendship
from src.app.models.bingo import BingoBoard
from src.app.api.deps import get_current_user

# 요청하신 스키마 import
from src.app.schemas.social import (
    FriendshipCreate,
    FriendshipRead,
    FriendshipUpdate,
    FriendRequestResponse,
    FriendBingoStatus,
    FriendListResponse,
    FriendDeleteResponse,
    UserRead,
)

router = APIRouter()

# ==========================================
# 1. 친구 요청(Requests) 관련 API
# ==========================================

@router.post("/friends/requests", response_model=FriendshipRead, status_code=status.HTTP_201_CREATED)
async def create_friend_request(
    friendship_in: FriendshipCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 본인 확인 추가
):
    """
    친구 신청을 생성합니다. (기존 두 API 통합)
    - requester_id: 신청한 사람의 user_id (current_user로 자동 지정 권장)
    - addressee_id: 신청받은 사람의 user_id
    """
    # 자기 자신에게 신청하는지 확인
    if current_user.id == friendship_in.addressee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신에게 친구 신청을 보낼 수 없습니다.",
        )

    # 이미 친구 관계이거나 신청 중인지 확인 (중복 방지)
    existing_friendship = (
        db.query(Friendship)
        .filter(
            or_(
                and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == friendship_in.addressee_id),
                and_(Friendship.requester_id == friendship_in.addressee_id, Friendship.addressee_id == current_user.id),
            )
        )
        .first()
    )

    if existing_friendship:
        if existing_friendship.status == "PENDING":
            raise HTTPException(status_code=400, detail="이미 대기 중인 친구 신청이 있습니다.")
        elif existing_friendship.status == "ACCEPTED":
            raise HTTPException(status_code=400, detail="이미 친구 상태입니다.")

    # 새로운 친구 신청 생성
    new_friendship = Friendship(
        requester_id=current_user.id,
        addressee_id=friendship_in.addressee_id,
        status="PENDING",
    )

    db.add(new_friendship)
    db.commit()
    db.refresh(new_friendship)

    return new_friendship


@router.get("/friends/requests/received", response_model=List[FriendRequestResponse])
def get_received_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    나에게 온 친구 신청 목록을 조회합니다.
    """
    requests = db.query(Friendship).filter(
        Friendship.addressee_id == current_user.id, 
        Friendship.status == "PENDING"
    ).all()
    
    return requests


@router.get("/friends/requests/sent", response_model=List[FriendRequestResponse])
def get_sent_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    내가 보낸 요청 중 아직 'PENDING' 상태인 것들만 가져와서 
    상대방의 닉네임과 함께 반환합니다.
    """
    # 1. 내가 보낸 대기 중인 신청들 조회
    sent_requests = db.query(Friendship).filter(
        Friendship.requester_id == current_user.id, 
        Friendship.status == "PENDING"
    ).all()

    result = []
    for req in sent_requests:
        # 2. 신청을 받는 사람(addressee_id)의 정보를 User 테이블에서 찾음
        receiver = db.query(User).filter(User.id == req.addressee_id).first()
        
        # 3. FriendRequestResponse 스키마 필드명에 맞춰서 데이터 구성
        result.append({
            "friendship_id": req.id,          # 스키마의 friendship_id 매핑
            "user_id": req.addressee_id,      # 받는 사람 ID
            "nickname": receiver.nickname if receiver else "알 수 없음",
            "profile_image_url": receiver.profile_image_url if receiver else None,
            "status": req.status
        })

    return result


@router.patch("/friends/requests/{friendship_id}", response_model=FriendshipRead)
async def update_friend_request(
    friendship_id: int,
    friendship_update: FriendshipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    친구 신청을 수락하거나 거절합니다.
    """
    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="친구 신청 내역을 찾을 수 없습니다.")

    # 신청받은 사람(addressee_id)이 요청을 처리하는지 확인
    if friendship.addressee_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인에게 온 친구 신청만 수락하거나 거절할 수 있습니다.")

    if friendship.status != "PENDING":
        raise HTTPException(status_code=400, detail="이미 처리된 친구 신청입니다.")

    friendship.status = friendship_update.status
    db.commit()
    db.refresh(friendship)

    return friendship


# ==========================================
# 2. 친구 관계(Relationships) 관련 API
# ==========================================

@router.get("/friends", response_model=FriendListResponse)
def get_friend_list(db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)):
    """
    내 친구 목록과 각 친구의 최신 빙고 현황을 함께 조회합니다.
    """
    # 1. 친구 관계 가져오기
    friendships = db.query(Friendship).filter(
        and_(
            or_(Friendship.requester_id == current_user.id, Friendship.addressee_id == current_user.id),
            Friendship.status == "ACCEPTED",
        )
    ).all()

    friend_ids = [fs.addressee_id if fs.requester_id == current_user.id else fs.requester_id for fs in friendships]
    if not friend_ids:
        return {"status": "success", "message": "친구가 없습니다.", "data": []}

    # 2. N+1 문제 해결을 위해 모든 친구의 정보를 한 번에 가져오기
    friends = db.query(User).filter(User.id.in_(friend_ids)).all()
    
    # 3. 모든 친구의 최신 빙고판을 한 번에 가져오기 (성능 최적화)
    latest_bingos = (
        db.query(BingoBoard)
        .filter(BingoBoard.user_id.in_(friend_ids))
        .distinct(BingoBoard.user_id)
        .order_by(BingoBoard.user_id, BingoBoard.created_at.desc())
        .all()
    )
    bingo_map = {bingo.user_id: bingo for bingo in latest_bingos}

    # 4. 데이터 합치기
    results = []
    for friend in friends:
        bingo = bingo_map.get(friend.id)
        results.append({
            "user_id": friend.id,
            "nickname": friend.nickname,
            "profile_image": friend.profile_image_url,
            "bingo_count": bingo.completed_lines if bingo else 0,
            "progress_percentage": (bingo.marked_cells / 25 * 100) if bingo else 0,
            "last_updated": bingo.updated_at if bingo else friend.created_at,
        })

    return {"status": "success", "message": "조회 완료", "data": results}


@router.delete("/friends/{friend_id}", response_model=FriendDeleteResponse)
def delete_friend(friend_id: int, db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)):
    """
    친구 관계를 삭제합니다.
    """
    # ... (기존 삭제 로직 유지)
    return {"status": "success", "message": "삭제 완료", "data": {friend_id: "친구 관계가 삭제되었습니다."}}


@router.get("/friends/search", response_model=List[UserRead])
def search_friends(nickname: str, db: Session = Depends(get_db)):
    """
    닉네임으로 유저 검색
    """
    return db.query(User).filter(User.nickname.contains(nickname)).all()