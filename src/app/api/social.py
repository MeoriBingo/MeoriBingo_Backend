from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from sqlalchemy import or_, and_
from src.app.core.database import get_db
from src.app.models.social import Friendship, BingoReaction
from src.app.schemas.social import (
    FriendshipCreate,
    FriendshipRead,
    FriendshipUpdate,
    FriendRequestRead,
    FriendBingoStatus,
    FriendListResponse,
    FriendDeleteResponse,
    ReactionCreate,
    ReactionRead,
)
from src.app.api import deps
from src.app.models.user import User
from src.app.models.bingo import BingoBoard
from src.app.api.deps import get_current_user


router = APIRouter()


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
def get_friend_requests(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    나에게 온 친구 신청 목록을 조회합니다.
    """
    # 내 ID가 addressee_id로 되어 있는 신청들 전부 찾아드려
    requests = (
        db.query(Friendship)
        .filter(
            Friendship.addressee_id == current_user.id, Friendship.status == "PENDING"
        )
        .all()
    )

    # 닉네임 합쳐서 리스트에 담아드려
    result = []

    for req in requests:
        sender = db.query(User).filter(User.id == req.requester_id).first()
        result.append(
            {
                "id": req.id,
                "requester_id": req.requester_id,
                "requester_nickname": sender.nickname if sender else "알 수 없음",
                "status": req.status,
                "created_at": req.created_at,
            }
        )

    return requests


# 친구 빙고판에 반응 남기기 (by지우)


@router.post("/friends/bingo/react", response_model=ReactionRead)
async def create_bingo_reaction(
    reaction_in: ReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    친구의 빙고판에 반응을 남깁니다.
    """
    # 1. 대상 빙고판이 존재하는지 확인
    target_board = (
        db.query(BingoBoard).filter(BingoBoard.id == reaction_in.bingo_board_id).first()
    )
    if not target_board:
        raise HTTPException(status_code=404, detail="빙고판을 찾을 수 없습니다.")

    # 2. 내 자신에게는 반응을 남길 수 없게 하거나(선택사항), 친구 사이인지 확인
    if target_board.user_id != current_user.id:
        is_friend = (
            db.query(Friendship)
            .filter(
                and_(
                    or_(
                        and_(
                            Friendship.requester_id == current_user.id,
                            Friendship.addressee_id == target_board.user_id,
                        ),
                        and_(
                            Friendship.requester_id == target_board.user_id,
                            Friendship.addressee_id == current_user.id,
                        ),
                    ),
                    Friendship.status == "ACCEPTED",
                )
            )
            .first()
        )

        if not is_friend:
            raise HTTPException(
                status_code=403, detail="친구의 빙고판에만 반응을 남길 수 있습니다."
            )
    # 3. 이미 해당 빙고판에 내가 남긴 리액션이 있는지 확인 (중복 방지)
    existing_reaction = db.query(BingoReaction).filter(
        BingoReaction.user_id == current_user.id,
        BingoReaction.bingo_board_id == reaction_in.bingo_board_id
    ).first()

    if existing_reaction:
        # 이미 있다면 새로운 리액션 타입으로 업데이트
        existing_reaction.reaction_type = reaction_in.reaction_type
        db.commit()
        db.refresh(existing_reaction)
        return existing_reaction
    
    # 4. 반응 저장
    new_reaction = BingoReaction(
        user_id=current_user.id,
        bingo_board_id=reaction_in.bingo_board_id,
        reaction_type=reaction_in.reaction_type,
    )
    db.add(new_reaction)
    db.commit()
    db.refresh(new_reaction)

    return new_reaction

# 친구 빙고판에 남긴 반응 취소하기 
@router.delete("/friends/bingo/react/{bingo_board_id}")
async def delete_bingo_reaction(
    bingo_board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    남겼던 반응을 취소(삭제)합니다.
    """
    reaction = db.query(BingoReaction).filter(
        BingoReaction.user_id == current_user.id,
        BingoReaction.bingo_board_id == bingo_board_id
    ).first()

    if not reaction:
        raise HTTPException(status_code=404, detail="삭제할 반응이 없습니다.")

    db.delete(reaction)
    db.commit()
    
    return {"message": "반응이 성공적으로 취소되었습니다."}


@router.get("/friends", response_model=FriendListResponse)
def get_friend_list(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)
):
    """
    내 친구 목록과 각 친구의 최신 빙고 현황을 함께 조회합니다.
    """
    # STEP 1: 나랑 연결된 '수락됨(ACCEPTED)' 상태의 친구 관계 모두 찾기
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

    # STEP 2: 친구 관계 데이터에서 '내가 아닌 상대방의 ID' 출력
    friend_ids = [
        fs.addressee_id if fs.requester_id == current_user.id else fs.requester_id
        for fs in friendships
    ]

    # 친구가 한 명도 없다면 바로 빈 결과 반환
    if not friend_ids:
        return {"status": "success", "message": "친구가 없습니다.", "data": []}

    # STEP 3: 골라낸 친구 ID들을 기반으로 유저 정보와 빙고 정보를 합치기
    results = []

    friends = db.query(User).filter(User.id.in_(friend_ids)).all()

    for friend in friends:
        # 각 친구의 가장 최근(최신순) 빙고판 하나를 가져옵니다.
        bingo = (
            db.query(BingoBoard)
            .filter(BingoBoard.user_id == friend.id)
            .order_by(BingoBoard.created_at.desc())
            .first()
        )

        # 친구의 기본 정보 + 빙고 현황 데이터를 합체!
        results.append(
            {
                "user_id": friend.id,
                "nickname": friend.nickname,
                "profile_image": friend.profile_image,
                "bingo_count": bingo.completed_lines if bingo else 0,
                "progress_percentage": (bingo.marked_cells / 25 * 100) if bingo else 0,
                "last_updated": bingo.updated_at if bingo else friend.created_at,
            }
        )

    return {
        "status": "success",
        "message": "친구 목록 및 빙고 현황 조회가 완료되었습니다.",
        "data": results,
    }


@router.delete("/friends/{friend_id}", response_model=FriendDeleteResponse)
def delete_friend(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    친구 관계를 삭제합니다. (나와 상대방 사이의 모든 관계 데이터 삭제)
    """
    # 1. 나와 상대방 사이의 Friendship 데이터를 찾기
    friendship = (
        db.query(Friendship)
        .filter(
            and_(
                or_(
                    and_(
                        Friendship.requester_id == current_user.id,
                        Friendship.addressee_id == friend_id,
                    ),
                    and_(
                        Friendship.requester_id == friend_id,
                        Friendship.addressee_id == current_user.id,
                    ),
                ),
                Friendship.status
                == "ACCEPTED",  # 이미 친구인 상태만 삭제 가능하도록 설정
            )
        )
        .first()
    )

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
        "message": "요청이 성공적으로 처리되었습니다.",
        "data": {friend_id: "친구 관계가 삭제되었습니다."},
    }
