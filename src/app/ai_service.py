import base64
import os
from openai import AzureOpenAI
from sqlalchemy.orm import Session
# (주의) 팀 프로젝트의 실제 모델 파일 경로에 맞춰 수정하세요.
# from src.app.models.mission import Mission 

def verify_image_mission(db: Session, cell_id: int, image_path: str):
    """
    DB에서 미션 정보를 가져와 OpenAI GPT-4o로 사진을 판독합니다.
    """
    # 1. DB에서 미션 정보 조회 (주신 Column들이 여기에 쓰입니다)
    # BingoCell과 Mission 테이블이 연결되어 있다고 가정합니다.
    target_mission = db.query(Mission).filter(Mission.id == cell_id).first()
    
    if not target_mission or target_mission.is_active == 0:
        return "INACTIVE_MISSION"

    # [중요] 주신 Column 데이터 추출
    m_title = target_mission.title       # 예: "텀블러 사용하기"
    m_category = target_mission.category # 예: "환경 보호"
    m_desc = target_mission.description  # 예: "텀블러가 잘 보이게 찍어주세요."

    # 2. 사진 파일을 Base64 문자열로 변환
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    # 3. Azure OpenAI 설정
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview"
    )

    # 4. AI에게 '카테고리'와 '제목'을 힌트로 주어 판독 요청
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[
            {
                "role": "system",
                "content": f"당신은 '{m_category}' 카테고리 미션의 전문 판독관입니다. "
                           f"사진 속에 '{m_title}'에 해당하는 물체나 행동이 있는지 확인하세요."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": f"미션 제목: {m_title}\n상세 설명: {m_desc}\n"
                                f"이 사진이 미션 성공인지 SUCCESS 또는 FAIL로만 답하세요."
                    },
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
                    }
                ]
            }
        ]
    )
    
    return response.choices[0].message.content.strip()



