import os
import json
import base64
import random
from datetime import datetime
from typing import List, Dict
from openai import AzureOpenAI
from dotenv import load_dotenv
from sqlalchemy import Column, BigInteger, String, Text, SmallInteger, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from src.app.models.mission import Mission

load_dotenv() 

Base = declarative_base()

class BingoAIService:
    def __init__(self):
        load_dotenv()
        
        print(f"DEBUG - Current Dir: {os.getcwd()}") # 현재 서버가 돌아가는 위치 출력
        print(f"DEBUG - API KEY EXISTS: {bool(os.getenv('AZURE_OPENAI_API_KEY'))}")

        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.api_version = "2024-12-01-preview"
        # 환경 변수가 누락되었는지 방어 코드 추가
        if not self.api_key or not self.endpoint:
            raise ValueError(".env 파일에서 AZURE_OPENAI 설정값을 찾을 수 없습니다. 파일 위치를 확인하세요.")
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=self.api_version
        )

    # 1. 빙고 미션 생성 (self 추가 및 들여쓰기 수정)
    def generate_bingo_missions(self, mode: str, selected_category: str) -> List[Dict]:
        """
        mode: 'normal' 또는 'challenge'
        selected_category: ['생산성', '활동성', '마인드셋', '성장성', '창의성'] 중 하나
        """
        all_categories = ["생산성", "활동성", "마인드셋", "성장성", "창의성"]
        # 챌린지 모드일 경우 제외할 나머지 카테고리 추출
        other_categories = [c for c in all_categories if c != selected_category]
     
        # 1. 범주별 핵심 정의
        category_definitions = """
        [목표 범주별 상세 가이드]
        1. **생산성** (효율과 결과)
        업무·학업 방해 요소 제거, 시간 관리, 가시적 성과 중심.
        인증 기준: 정리된 공간, 작성 완료된 목록, 타이머·플래너 등 도구의 세팅 상태.
        2. **활동성** (에너지와 체력)
        신체적 움직임, 활력 충전, 가벼운 스트레칭·운동 관련 활동 중심.
        인증 기준: 운동 도구, 스트레칭 후 놓인 매트, 물병·간식 등 활동 전후 사물.
        3. **마인드셋** (회복과 중심성)
        내면의 평화, 스트레스 관리, 정신적 에너지 충전 중심.
        인증 기준: 세팅된 휴식 공간, 차·향초 등 이완 도구, 손으로 적은 짧은 메모.
        4. **성장성** (확장과 깊이)
        지식 습득, 역량 강화, 자기계발·필사·독서 중심.
        인증 기준: 펼쳐진 책·노트, 필사한 문장이 적힌 종이, 밑줄 그은 페이지.
        5. **창의성** (재미와 실험)
        손으로 직접 만들거나 꾸미는 소규모 결과물 중심.
        낙서, 스크랩, 색칠, 메모 꾸미기, 재료 배치 등 10분 안에 완성되는 유형의 산출물이 남는 활동.
        인증 기준: 직접 손댄 결과물(낙서장, 오린 조각, 색칠한 종이, 꾸민 포스트잇 등)이 사진에 찍혀야 함.
        ※ 아이디어를 "떠올리는" 것이 아니라 무언가를 "건드린 흔적"이 반드시 찍혀야 함.
        """
     
        # 2. 모드별 미션 구성 지시문 생성
        if hasattr(mode, "value"):
            current_mode = str(mode.value).lower()
        else:
            current_mode = str(mode).lower()

        if "challenge" in current_mode:
            mission_composition = (
                f"1. '{selected_category}' 카테고리에서 3개의 미션을 생성하세요.\n"
                f"2. 나머지 카테고리({', '.join(other_categories)}) 중에서 랜덤하게 총 6개의 미션을 생성하세요."
            )
        else:  # normal 모드
            mission_composition = f"9개 미션 모두 '{selected_category}' 카테고리로 생성하세요."
       
        # 3. 프롬프트 작성
        system_prompt = f"""
        당신은 'AI 빙고 미션' 생성기입니다. 다음 원칙을 반드시 준수하여 9개의 미션을 생성하세요.
     
        [미션 설계 원칙]
        1. 퀵 윈(Quick Win): 30분 이내 수행 가능할 것.
        2. 사물 중심(Object-Oriented): 정지된 사물 상태가 찍혀야 함. "~하는 모습"이나 추상적 인증 금지.
        3. 인증 직관성: 사진 한 장으로 성공 여부를 즉시 판별할 수 있는 피사체 제시.
        4. 미션 직관성 : 카테고리에 해당하는 옵션에 맞는 미션 제시하기.
     
        [미션 구성 지시]
        {mission_composition}
     
        [출력 형식]
        JSON 형식으로 'missions' 키 아래에 배열을 담아 반환하세요.
        필드명: title, description, category
        """
     
        try:
            # self.client로 수정
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{mode} 모드에 맞는 빙고판을 구성해줘."}
                ],
                response_format={"type": "json_object"},
                temperature = 0.9,
                presence_penalty = 1.5
            )
     
            result = json.loads(response.choices[0].message.content)
            return result.get("missions", [])
     
        except Exception as e:
            print(f"Error: {e}")
            return []
     
            
    # 2. 빙고 이미지 판별 (self 추가 및 들여쓰기 수정)
    def verify_image_mission(self, db: Session, mission_id: int, image_path: str):
        """
        DB에서 미션 정보를 가져와 Azure OpenAI(GPT-4o)로 사진을 판독합니다.
        """
        target_mission = db.query(Mission).filter(Mission.id == mission_id).first()
        
        if not target_mission:
            return "MISSION_NOT_FOUND"
            
        if target_mission.is_active == 0:
            return "INACTIVE_MISSION"

        m_title = target_mission.title
        m_category = target_mission.category
        m_desc = target_mission.description

        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            return "IMAGE_FILE_NOT_FOUND"

        try:
            # self.client 사용
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"당신은 '{m_category}' 카테고리 미션의 전문 판독관입니다. "
                            f"제시된 사진 속에 '{m_desc}' 미션에 해당하는 명확한 피사체가 있는지 확인하세요."
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"미션 제목: {m_title}\n"
                                    f"상세 설명: {m_desc}\n\n"
                                    "위 설명에 따라 이 사진이 미션 성공인지 판단하세요. "
                                    "판단 결과는 다른 설명 없이 오직 'SUCCESS' 또는 'FAIL'로만 답하세요."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=10,
                temperature=0 
            )
            
            return response.choices[0].message.content.strip().upper()
            
        except Exception as e:
            print(f"AI Verification Error: {e}")
            return "ERROR_DURING_VERIFICATION"

    # 3. 빙고 문구 생성 (self 추가 및 들여쓰기 수정)
    def request_openai(self, mission_obj, lines=0, streak=1, weather="맑음", completed_at=None, histories=[]):
        if completed_at is None:
            completed_at = datetime.now()
        current_date = completed_at.strftime("%Y-%m-%d")
        current_time = completed_at.strftime("%H:%M")
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        current_weekday = weekdays[completed_at.weekday()]

        achievement_type = "BINGO" if lines > 0 else "SINGLE_MISSION"

        context_pool = {
            "streak": f"{streak}일 연속",
            "day_of_week": current_weekday,
            "time": current_time,
            "weather": weather,
        }
        selected_keys = random.sample(list(context_pool.keys()), 2)
        selected_context = {k: context_pool[k] for k in selected_keys}

        tone = random.choice(["유머러스", "진중함", "활기찬", "따뜻함"])
        context_text = ", ".join(f"{k}({v})" for k, v in selected_context.items())

        system_content = f"""너는 'AI 빙고 미션' 서비스의 개인 전담 코치이자 전문 카피라이터야.
사용자의 달성 상황({achievement_type})에 맞춰 아래 규칙에 따라 축하 문구를 작성해.

[문구 작성 규칙]
1. 응원 포인트:
   - SINGLE_MISSION: 미션 제목 [{mission_obj.title}]이라는 구체적 행위 자체를 격하게 칭찬할 것.
   - BINGO: [{mission_obj.category}] 범주의 성격과 [{lines}줄 빙고 완성] 성취에 집중해 칭찬할 것.
2. 이번 문구에 사용할 톤: {tone}
3. 이번 문구에 반드시 포함할 상황 요소: {context_text}
4. 문구만 출력 (1~2문장), 톤 이름이나 상황 키값은 절대 표시하지 말 것.
"""
        user_content = f"""
[달성 데이터]
- 타입: {"빙고 완성" if achievement_type == "BINGO" else "미션 완료"}
- 미션 제목: {mission_obj.title}
- 미션 범주: {mission_obj.category}
- 빙고 상태: {f"{lines}줄 완성" if lines > 0 else "미션 클리어"}
- 달성 시점: {current_date} ({current_weekday}) {current_time}
- 현재 날씨: {weather}
- 연속 기록: {streak}일 연속 달성 중

위 데이터를 바탕으로 유저에게 힘이 되는 축하 문구를 작성해줘.
"""

        messages = [{"role": "system", "content": system_content}]
        messages.extend(histories)
        messages.append({"role": "user", "content": user_content})

        # self.client 사용
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0.9,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()