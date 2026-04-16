from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import or_, and_
from src.app.core.database import get_db
from src.app.models.social import Friendship  # 우리가 찾은 모델!
from src.app.models.social import Friendship 
from src.app.schemas.social import (
    FriendRequestRead, 
    FriendBingoStatus, 
    FriendListResponse, 
    FriendDeleteResponse  
)
from src.app.models.user import User  
from src.app.models.bingo import BingoBoard
from src.app.api import deps

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

@router.get("/friends", response_model=FriendListResponse)
def get_friend_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    내 친구 목록과 각 친구의 최신 빙고 현황을 함께 조회합니다.
    """
    # STEP 1: 나랑 연결된 '수락됨(ACCEPTED)' 상태의 친구 관계 모두 찾기
    friendships = db.query(Friendship).filter(
        and_(
            or_(
                Friendship.requester_id == current_user.id,
                Friendship.addressee_id == current_user.id
            ),
            Friendship.status == "ACCEPTED"
        )
    ).all()

    # STEP 2: 친구 관계 데이터에서 '내가 아닌 상대방의 ID' 출력
    friend_ids = [
        fs.addressee_id if fs.requester_id == current_user.id else fs.requester_id 
        for fs in friendships
    ]

    # 친구가 한 명도 없다면 바로 빈 결과 반환
    if not friend_ids:
        return {
            "status": "success",
            "message": "친구가 없습니다.",
            "data": []
        }

    # STEP 3: 골라낸 친구 ID들을 기반으로 유저 정보와 빙고 정보를 합치기
    results = []
    
    friends = db.query(User).filter(User.id.in_(friend_ids)).all()

    for friend in friends:
        # 각 친구의 가장 최근(최신순) 빙고판 하나를 가져옵니다.
        bingo = db.query(BingoBoard).filter(
            BingoBoard.user_id == friend.id
        ).order_by(BingoBoard.created_at.desc()).first()
        
        # 친구의 기본 정보 + 빙고 현황 데이터를 합체!
        results.append({
            "user_id": friend.id,
            "nickname": friend.nickname,
            "profile_image": friend.profile_image,
            "bingo_count": bingo.completed_lines if bingo else 0,
            "progress_percentage": (bingo.marked_cells / 25 * 100) if bingo else 0,
            "last_updated": bingo.updated_at if bingo else friend.created_at
        })

    return {
        "status": "success",
        "message": "친구 목록 및 빙고 현황 조회가 완료되었습니다.",
        "data": results
    }
@router.delete("/friends/{friend_id}", response_model=FriendDeleteResponse)
def delete_friend(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    친구 관계를 삭제합니다. (나와 상대방 사이의 모든 관계 데이터 삭제)
    """
    # 1. 나와 상대방 사이의 Friendship 데이터를 찾기
    friendship = db.query(Friendship).filter(
        and_(
            or_(
                and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == friend_id),
                and_(Friendship.requester_id == friend_id, Friendship.addressee_id == current_user.id)
            ),
            Friendship.status == "ACCEPTED"  # 이미 친구인 상태만 삭제 가능하도록 설정
        )
    ).first()

    # 2. 만약 친구 관계가 없다면 404 에러를 던지기
    if not friendship:
        raise HTTPException(status_code=404, detail="친구 관계를 찾을 수 없습니다.")

    # 3. 데이터 삭제 수행
    try:
        db.delete(friendship)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="친구 삭제 중 오류가 발생했습니다.")

    return {
        "status": "success",
        "message": "친구 삭제가 완료되었습니다.",
        "data": {"deleted_friend_id": friend_id}
    }