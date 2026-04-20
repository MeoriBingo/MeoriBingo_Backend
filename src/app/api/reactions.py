from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional

# Core & Utils
from src.app.core.database import get_db
from src.app.api import deps
from src.app.api.deps import get_current_user

# Models
from src.app.models.user import User
from src.app.models.social import Friendship, BingoReaction # BingoReaction 추가됨
from src.app.models.bingo import BingoBoard

# Schemas
from src.app.schemas.social import (
    # 유저 관련
    UserRead,
    
    # 친구 요청 관련
    FriendshipCreate,
    FriendshipRead,
    FriendshipUpdate,
    FriendRequestResponse,
    
    # 친구 목록/빙고 현황 관련
    FriendBingoStatus,
    FriendListResponse,
    FriendDeleteResponse,
    
    # 리액션 관련 
    ReactionCreate,
    ReactionRead
)

router = APIRouter()

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
