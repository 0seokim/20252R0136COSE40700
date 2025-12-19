from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routers.ui import router as ui_router
from app.routers.exchange import router as exchange_router
from app.routers.news import router as news_router
from app.routers.backup import router as backup_router

app = FastAPI(title="Economy Backend API", version="1.1.0")

# static
app.mount("/static", StaticFiles(directory="static"), name="static")

# routers
app.include_router(ui_router)
app.include_router(exchange_router, prefix="/exchange", tags=["exchange"])
app.include_router(news_router, prefix="/news", tags=["news"])
app.include_router(backup_router, tags=["backup"])

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["health"])
def health():
    return {"ok": True}
