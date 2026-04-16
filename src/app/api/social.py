from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import or_, and_
from src.app.core.database import get_db
from src.app.models.social import Friendship  # 우리가 찾은 모델!
from src.app.schemas.social import FriendRequestRead,FriendBingoStatus,FriendListResponse # 방금 만든 접시!
from src.app.api import deps
from src.app.models.user import User  
from src.app.models.bingo import BingoBoard
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

@router.get("/friends/bingo", response_model=List[FriendBingoStatus])
async def get_friends_bingo_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # 1. 친구 목록 조회 (내가 요청했거나, 요청받았거나 둘 다 포함)
    friends_query = db.query(Friendship).filter(
        and_(
            or_(
                Friendship.requester_id == current_user.id,
                Friendship.addressee_id == current_user.id
            ),
            Friendship.status == "ACCEPTED"
        )
    ).all()

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
        bingo = db.query(BingoBoard).filter(BingoBoard.user_id == f_id).order_by(BingoBoard.created_at.desc()).first()
        
        if friend:
            results.append({
                "user_id": friend.id,
                "nickname": friend.nickname,
                "profile_image": friend.profile_image,
                "bingo_count": bingo.completed_lines if bingo else 0,
                "progress_percentage": (bingo.marked_cells / 25 * 100) if bingo else 0,
                "last_updated": bingo.updated_at if bingo else friend.created_at
            })
    return results

@router.get("/friends/me", response_model=FriendListResponse)
def get_friend_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    내 친구 목록을 조회합니다.
    """
    # STEP 1: ACCEPTED 친구 관계 조회
    friendships = db.query(Friendship).filter(
        and_(
            or_(
                Friendship.requester_id == current_user.id,
                Friendship.addressee_id == current_user.id
            ),
            Friendship.status == "ACCEPTED"
        )
    ).all()

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
            "data": []
        }

    # STEP 4: 친구들 정보 가져오기
    friends = db.query(User).filter(User.id.in_(friend_ids)).all()

    return {
        "status": "success",
        "message": "요청이 성공적으로 처리되었습니다.",
        "data": friends
    }