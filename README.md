# MeoriBingo 프로젝트

## 디렉토리 구조

```
/
├── src/
│     ├── app/             # 전체 애플리케이션 소스 코드
│     ├── api/             # API 라우터 정의
│     ├── core/            # 설정, 보안 등 핵심 기능
│     ├── models/          # 데이터베이스 모델
│     ├── schemas/         # Pydantic 데이터 검증 모델
│     ├── db_conn_test.py  # MySQL 접속 테스트
│     └── main.py          # 서버 실행 진입점 (FastAPI 인스턴스 초기화)
├── requirements.txt       # 프로젝트 필수 라이브러리 목록
├── .env                   # 환경 변수 설정 파일
└── README.md              # 프로젝트 설치 및 실행 가이드
```

## 주요 파일 내용

- src/app/main.py: 기본 파일
- requirements.txt: fastapi, uvicorn, python-dotenv, pydantic 등 필수 라이브러리 추가

## 실행 방법 (요약)

1. 가상환경 생성 및 활성화
   - python -m venv .venv
2. 가상환경 활성화
   - Windows: .venv\Scripts\activate
   - Mac: source .venv/bin/activate
3. 의존성 설치
   - pip install -r requirements.txt
4. 서버 실행
   - uvicorn src.app.main:app --reload
5. Swagger UI 확인
   - 브라우저에서 http://127.0.0.1:8000/docs 접속
