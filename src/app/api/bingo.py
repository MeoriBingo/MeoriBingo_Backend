from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime
from src.app.core.database import get_db
from src.app.models.bingo import BingoBoard, BingoCell
from src.app.models.mission import Mission
from src.app.schemas.bingo import BingoGenerateRequest, BingoBoardResponse

router = APIRouter(prefix="/bingo", tags=["Bingo"])


@router.post("/generate", response_model=BingoBoardResponse)
async def generate_bingo_board(
    request: BingoGenerateRequest, db: Session = Depends(get_db)
):
    """
    새로운 빙고판을 생성합니다.
    1. bingo_board 테이블에 새로운 레코드 삽입
    2. missions 테이블에서 랜덤으로 9개 미션 선택
    3. bingo_cells 테이블에 9개 미션을 각 위치(1~9)에 배치
    """
    try:
        # 빙고판 생성
        new_board = BingoBoard(
            user_id=request.user_id,
            mode="NORMAL",
            status="IN_PROGRESS",
            completed_count=0,
        )
        db.add(new_board)
        db.flush()  # board.id를 얻기 위해 flush 실행

        # 랜덤 미션 9개 선택
        random_missions = (
            db.query(Mission)
            .filter(Mission.is_active == 1)
            .order_by(func.rand())
            .limit(9)
            .all()
        )

        if len(random_missions) < 9:
            raise HTTPException(
                status_code=400,
                detail="빙고판을 만들기 위한 활성화 된 미션 9개 조회 실패",
            )

        # 빙고 셀 생성
        bingo_cells = []
        for i, mission in enumerate(random_missions):
            new_cell = BingoCell(
                board_id=new_board.id,
                mission_id=mission.id,
                position=i + 1,  # 1부터 9까지
                status="IN_PROGRESS",  # 사용자 요청에 따른 상태값
                is_completed=0,  # 아직 완료되지 않음
            )
            db.add(new_cell)
            bingo_cells.append(new_cell)

        db.commit()
        db.refresh(new_board)

        # 응답 모델 구성을 위해 cells 추가 (Relationship이 모델에 정의되어 있지 않을 경우 대비)
        new_board.cells = bingo_cells
        return new_board

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Failed to generate bingo board: {str(e)}"
        )


@router.patch("/cells/{cell_id}")
async def update_bingo_cell_completion(cell_id: int, db: Session = Depends(get_db)):
    """
    특정 빙고 셀의 상태를 완료(COMPLETED)로 업데이트합니다.
    - status: 'COMPLETED'
    - is_completed: 1
    - completed_at: 현재 시간
    """
    cell = db.query(BingoCell).filter(BingoCell.id == cell_id).first()

    if not cell:
        raise HTTPException(status_code=404, detail="Bingo cell not found")

    try:
        cell.status = "COMPLETED"
        cell.is_completed = 1
        cell.completed_at = datetime.now()

        db.commit()
        db.refresh(cell)

        return {
            "message": "Bingo cell updated successfully",
            "cell_id": cell.id,
            "status": cell.status,
            "is_completed": cell.is_completed,
            "completed_at": cell.completed_at,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update bingo cell: {str(e)}"
        )
