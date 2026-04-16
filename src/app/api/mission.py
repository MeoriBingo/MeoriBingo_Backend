import os
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from azure.storage.blob import BlobServiceClient

# 프로젝트 구조에 맞춘 import
from src.app.core.database import get_db 
from src.app.models.mission import Mission 
from src.app.schemas.mission import MissionVerifyResponse, MissionResponse

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