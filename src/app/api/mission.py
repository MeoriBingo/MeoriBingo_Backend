import os
import uuid

from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from azure.storage.blob import BlobServiceClient
from src.app.schemas.mission import MissionVerifyResponse, MissionResponse, MissionGuideRead
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.models.mission import Mission


router = APIRouter(prefix="/mission", tags=["Mission"])

# Azure Storage 설정
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "mission-images")

@router.post("/verify", response_model=MissionVerifyResponse)
async def picture_upload(file: UploadFile = File(...)):
    """
    미션 사진을 Azure Storage에 업로드합니다.
    """
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise HTTPException(
            status_code=500, detail="Azure Storage connection string is not configured"
        )

    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file extension")

    try:
        unique_filename = f"mission/user_id/{uuid.uuid4()}{file_ext}"
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=unique_filename)

        contents = await file.read()
        blob_client.upload_blob(contents, overwrite=True)

        return MissionVerifyResponse(
            message="Successfully uploaded", 
            image_url=blob_client.url, 
            is_success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to Azure: {str(e)}")

@router.get("/missions", response_model=List[MissionResponse]) # 스키마 적용
async def get_missions(db: Session = Depends(get_db)):
    """
    DB에서 미션 목록을 전체 조회하여 반환합니다.
    """
    try:
        missions = db.query(Mission).all()
        return missions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"데이터베이스 조회 중 오류 발생: {str(e)}"
        )



# 미션 가이드 조회 서비스(by.서현)

@router.get("/{mission_id}/guide", response_model=MissionGuideRead)
def get_mission_guide(mission_id: int, db: Session = Depends(get_db)):
    """
    특정 미션 클릭시 "어떻게 찍으세요"라는 가이드 문구/이미지를 반환합니다.
    """

    #Mission 모델에서 mission_id로 데이터 조회
    my_mission_data = db.query(Mission).filter(Mission.id==mission_id).first()

    #만약 찾는 미션이 없으면 에러 생성
    if my_mission_data is None:
        raise HTTPException(status_code=404, detail="해당 미션을 찾을 수 없습니다.")
    
    #MissionGuideRead에 잘 담아서 프론트로 전송
    return MissionGuideRead(
        guideText=f"[{my_mission_data.title}] {my_mission_data.description}",
        # guideImage=저희 가이드 이미지도 하기로 했었나욥...?
        tips=(f"{my_mission_data.target_object}를 촬영하여 업로드하세요!")
        ### tips에 'xxx'을 촬영하세요 일단 이런식으로 해두겠습니다
    )
