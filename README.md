# 20252R0136COSE40700  
## COSE40700 Final Assignment – Economic Data Backend System

---

## 📌 Project Overview

**환율 데이터와 경제 뉴스를 수집·저장·조회·백업**
**FastAPI 기반 백엔드 시스템**

외부 공개 API를 활용하여 최신 경제 데이터를 주기적으로 수집하고,  
이를 데이터베이스에 저장한 뒤 REST API 및 간단한 UI를 통해 제공합니다.  
또한 Docker, Docker Compose, Kubernetes를 활용하여  
**배포 및 자동 백업이 가능한 운영 환경**을 구성합니다.


---

## ✨ Key Features

### 📈 Exchange Rate Service
- 최근 N일간 환율 데이터 제공
- 지원 통화:
  - USD → KRW
  - EUR → KRW
  - JPY → KRW
  - 100 JPY → KRW
- 외부 환율 API 기반 데이터 수집
- 데이터베이스 저장 후 조회

### 📰 Economic News Service
- 한국·미국 경제 뉴스 중심 수집
- Reuters, Bloomberg, WSJ, FT 등 **신뢰 가능한 주요 언론사** 위주 필터링
- GDELT API 기반 뉴스 수집
- 중복 기사 제거 후 DB 저장

### 💾 Database
- SQLite + SQLAlchemy ORM
- 자동 테이블 생성
- 컨테이너/재시작 환경에서도 데이터 유지 가능

### 🗂 Backup System
- API 기반 수동 백업 기능
- 날짜별 디렉토리 구조로 백업 파일 저장
- Docker Compose / Kubernetes CronJob 기반 **주 1회 자동 백업**

### 🚀 Deployment
- Local 개발 환경
- Docker 단일 컨테이너
- Docker Compose (API + Scheduler)
- Kubernetes (Deployment / Service / PVC / CronJob)

---

## ▶ How to Run the Project

### 1. Local 실행 (개발용)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
