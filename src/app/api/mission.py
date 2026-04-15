import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from azure.storage.blob import BlobServiceClient
from src.app.schemas.mission import MissionVerifyResponse

router = APIRouter(prefix="/mission", tags=["Mission"])

# Azure Storage 설정
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "mission-images")


@router.post("/verify", response_model=MissionVerifyResponse)
async def picture_upload(file: UploadFile = File(...)):
    """
    미션 사진을 Azure Storage에 업로드합니다.
    - 파일 이름을 고유하게 생성하여 업로드
    - 업로드된 사진의 URL 반환
    """
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise HTTPException(
            status_code=500, detail="Azure Storage connection string is not configured"
        )

    # 허용되는 이미지 확장자 확인
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file extension")

    try:
        # 고유한 파일 이름 생성
        unique_filename = f"mission/user_id/{uuid.uuid4()}{file_ext}"

        # BlobServiceClient 생성
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )
        blob_client = blob_service_client.get_blob_client(
            container=AZURE_CONTAINER_NAME, blob=unique_filename
        )

        # 파일 업로드
        contents = await file.read()
        blob_client.upload_blob(contents, overwrite=True)

        # 업로드된 파일의 URL (Azure Portal에서 컨테이너의 익명 접근 권한 설정 필요)
        image_url = blob_client.url

        return MissionVerifyResponse(
            message="Successfully uploaded", image_url=image_url, is_success=True
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload to Azure: {str(e)}"
        )
