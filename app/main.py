from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.exchange import router as exchange_router
from app.routers.news import router as news_router
from app.routers.ui import router as ui_router

app = FastAPI(title="Economy Backend API", version="1.0.0")

# 정적 파일 서빙 (index.html 및 기타 파일)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록
app.include_router(ui_router)                
app.include_router(exchange_router, prefix="/exchange", tags=["exchange"])
app.include_router(news_router, prefix="/news", tags=["news"])


@app.get("/health", tags=["health"])
def health():
    return {"ok": True}
