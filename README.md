# Coupang Review Analysis

리뷰 수집부터 머신러닝 분석, 시각화 대시보드까지 구현하는 통합 이커머스 리뷰 분석 시스템

---

## 0. 프로젝트 목표 (Project Goals)

**Coupang Review Analysis** 프로젝트의 목표는 다음과 같습니다:

### • 리뷰 데이터 자동 수집

쿠팡 웹사이트에서 상품 키워드 기반으로 리뷰 데이터를 크롤링합니다.

### • 데이터 정제 및 DB 저장

수집된 리뷰 데이터를 정제(ETL)하여 MySQL 데이터베이스에 저장합니다.

### • 리뷰 분석 (감성 분석 / 요약)

리뷰 텍스트에 머신러닝 분석을 적용하여 긍정/부정 감성 또는 요약 정보를 제공합니다.

### • 대시보드 시각화 제공

웹 UI에서 분석 결과를 직관적으로 확인할 수 있는 대시보드를 제공합니다.

### • 모듈화 & 확장성

Naver 등 타 플랫폼 리뷰도 쉽게 추가할 수 있도록 모듈화된 구조로 설계합니다.

---

## 1. 프로젝트 구조 (Project Structure)

```
coupang_review_analysis/
├── src/
│   ├── api/                  # 웹 UI API (Flask/FastAPI)
│   ├── crawler/              # 크롤러 모듈 (쿠팡, 네이버 등)
│   ├── dashboard/            # Streamlit 대시보드
│   ├── db/                   # MySQL 연동 모듈
│   ├── etl/                  # 데이터 전처리/정제
│   ├── ml/                   # 리뷰 감성분석/요약 모델
│   ├── utils/                # 로깅 및 공통 함수
│   └── config.py             # 설정 로더
├── main.py                   # 전체 파이프라인 실행
├── requirements.txt          # 의존성 목록
├── .env                      # 보안 정보 환경 변수
```

---

## 2. 데이터베이스 스키마 (MySQL Schema)

### 📁 리뷰 저장 테이블: `reviews`

| 컬럼명                 | 설명            |
| ------------------- | ------------- |
| product\_name       | 상품명           |
| brand               | 브랜드           |
| price               | 가격            |
| product\_id         | 쿠팡 상품번호       |
| options             | 옵션 정보         |
| review\_title       | 리뷰 제목         |
| review\_body        | 리뷰 본문         |
| review\_page        | 리뷰 페이지 번호     |
| author              | 작성자           |
| rating              | 평점            |
| review\_date        | 작성일           |
| seller              | 판매자           |
| real\_product\_name | 실제 구매 상품명     |
| images              | 이미지 URL 목록    |
| survey              | 리뷰 설문 응답 정보   |
| helpful\_count      | 도움됨 수         |
| sentiment           | (ML) 감성 분석 결과 |

---

## 3. 데이터 흐름 (Data Flow)

### 1. 키워드 입력 (Web UI)

사용자가 웹 UI에 키워드를 입력하여 크롤러 시작

### 2. 리뷰 수집 (크롤러)

`crawler/coupang_crawler.py`에서 리뷰 수집 및 메타 정보 추출

### 3. ETL 처리 및 저장

`etl/transformer.py`로 정제 후 → `db/database_handler.py` 통해 MySQL 저장

### 4. ML 분석

`ml/review_model.py`에서 리뷰 감성 분석 또는 요약 수행 → DB에 결과 추가

### 5. 시각화 대시보드

`dashboard/app.py` (Streamlit 기반)에서 리뷰 통계 및 분석 결과 시각화

---

## 4. Streamlit 대시보드 구성 예시

* 상품별 리뷰 수 및 평균 평점 (Bar chart)
* 긍정/부정 비율 (Pie chart)
* 주요 키워드 WordCloud
* 시간 흐름에 따른 리뷰 추이 (Line chart)
* 감성별 대표 리뷰 예시 출력

---

## 5. 실행 방법 (Run Instructions)

### 1. 가상환경 생성

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일에 다음 항목 포함:

```
DB_HOST=...
DB_USER=...
DB_PASS=...
DB_NAME=...
PROXY_URL=...
AUTH_KEY=...
```

### 3. 실행

```bash
python main.py          # 전체 파이프라인 실행
streamlit run src/dashboard/app.py   # 대시보드 실행
```

---

## 6. 향후 계획 (Future Work)

* [ ] 네이버 리뷰 크롤러(`naver_parser.py`) 모듈 추가
* [ ] 리뷰 요약 모델 추가 (Huggingface 기반)
* [ ] 작성자 마스킹 및 이미지 필터링 등 개인정보 보호 강화
* [ ] 주제 분류 모델 추가 (배송/품질/가격 등)

---

## 7. 기술 스택 (Tech Stack)

| 영역     | 기술                           |
| ------ | ---------------------------- |
| 백엔드    | Python 3.12, Flask / FastAPI |
| 크롤링    | Selenium, BeautifulSoup      |
| ETL    | Pandas, Custom Logic         |
| 데이터베이스 | MySQL, SQLAlchemy            |
| ML     | Transformers, KoELECTRA 등    |
| 대시보드   | Streamlit                    |
| 설정 관리  | python-dotenv (`.env`)       |

---

## 8. .gitignore 필수 항목

```
venv/
.env
__pycache__/
*.pyc
*.db
exports/
logs/
```

---
