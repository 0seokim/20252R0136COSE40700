# ---- Base image ----
FROM python:3.11-slim

# ---- Environment ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---- Workdir ----
WORKDIR /app

# 빌드 속도/호환성 향상용 시스템 패키지
# httpx는 보통 필요 없지만, 일부 패키지 빌드가 필요할 때를 대비해 최소 구성
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ---- Install dependencies ----
# requirements.txt를 쓰는 걸 권장
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ---- Copy source ----
COPY . /app

# ---- Expose port ----
EXPOSE 8000

# ---- Start ----
# app.main:app  =>  (파일) app/main.py 안의 FastAPI 인스턴스 이름이 app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
