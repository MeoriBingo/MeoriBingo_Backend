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
    current_user: User = Depends(get_current_user)
):
    """
    친구 신청을 보냅니다. (중복 신청 방지 로직 포함)
    """
    if current_user.id == friendship_in.addressee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신에게 친구 신청을 보낼 수 없습니다.",
        )

    # 중복 확인 (이미 친구거나, 신청 중인지)
    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == friendship_in.addressee_id),
            and_(Friendship.requester_id == friendship_in.addressee_id, Friendship.addressee_id == current_user.id)
        )
    ).first()

    if existing:
        if existing.status == "PENDING":
            raise HTTPException(status_code=400, detail="이미 대기 중인 친구 신청이 있습니다.")
        elif existing.status == "ACCEPTED":
            raise HTTPException(status_code=400, detail="이미 친구 상태입니다.")

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
    
    result = []
    for req in requests:
        sender = db.query(User).filter(User.id == req.requester_id).first()
        result.append({
            "friendship_id": req.id,
            "user_id": req.requester_id,
            "nickname": sender.nickname if sender else "알 수 없음",
            "profile_image_url": sender.profile_image_url if sender else None,
            "status": req.status
        })
    return result


@router.get("/friends/requests/sent", response_model=List[FriendRequestResponse])
def get_sent_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    내가 보낸 친구 신청 목록을 조회합니다.
    """
    sent_requests = db.query(Friendship).filter(
        Friendship.requester_id == current_user.id, 
        Friendship.status == "PENDING"
    ).all()

    result = []
    for req in sent_requests:
        receiver = db.query(User).filter(User.id == req.addressee_id).first()
        result.append({
            "friendship_id": req.id,
            "user_id": req.addressee_id,
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
    친구 신청 수락/거절
    """
    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship or friendship.addressee_id != current_user.id:
        raise HTTPException(status_code=403, detail="권한이 없거나 존재하지 않는 요청입니다.")

    if friendship.status != "PENDING":
        raise HTTPException(status_code=400, detail="이미 처리된 요청입니다.")

    friendship.status = friendship_update.status
    db.commit()
    db.refresh(friendship)
    return friendship


# ==========================================
# 2. 친구 관계 및 검색 API
# ==========================================

@router.get("/friends", response_model=FriendListResponse)
def get_friend_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    내 친구 목록과 빙고 현황 조회
    """
    friendships = db.query(Friendship).filter(
        and_(
            or_(Friendship.requester_id == current_user.id, Friendship.addressee_id == current_user.id),
            Friendship.status == "ACCEPTED",
        )
    ).all()

    friend_ids = [fs.addressee_id if fs.requester_id == current_user.id else fs.requester_id for fs in friendships]
    
    if not friend_ids:
        return {"status": "success", "message": "친구가 없습니다.", "data": []}

    friends = db.query(User).filter(User.id.in_(friend_ids)).all()
    
    # N+1 문제 방지를 위해 최신 빙고판 한 번에 조회
    latest_bingos = db.query(BingoBoard).filter(BingoBoard.user_id.in_(friend_ids)).all()
    bingo_map = {b.user_id: b for b in latest_bingos}

    results = []
    for friend in friends:
        bingo = bingo_map.get(friend.id)
        results.append({
            "user_id": friend.id,
            "nickname": friend.nickname,
            "profile_image": friend.profile_image_url,
            # DB 컬럼 completed_lines가 있어야 함! (없을 경우 0으로 기본값 처리)
            "bingo_count": getattr(bingo, "completed_lines", 0) if bingo else 0,
            "progress_percentage": (bingo.completed_count / 9 * 100) if bingo else 0,
            "last_updated": bingo.updated_at if bingo else friend.created_at,
        })
    return {"status": "success", "message": "조회 완료", "data": results}


@router.delete("/friends/{friend_id}", response_model=FriendDeleteResponse)
def delete_friend(friend_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    친구 삭제
    """
    friendship = db.query(Friendship).filter(
        and_(
            or_(
                and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == friend_id),
                and_(Friendship.requester_id == friend_id, Friendship.addressee_id == current_user.id)
            ),
            Friendship.status == "ACCEPTED"
        )
    ).first()

    if not friendship:
        raise HTTPException(status_code=404, detail="친구 관계를 찾을 수 없습니다.")

    db.delete(friendship)
    db.commit()
    return {"status": "success", "message": "삭제 완료", "data": {"deleted_id": friend_id}}


@router.get("/friends/search", response_model=List[UserRead])
def search_friends(nickname: str, db: Session = Depends(get_db)):
    """
    닉네임으로 유저 검색
    """
    return db.query(User).filter(User.nickname.contains(nickname)).all()