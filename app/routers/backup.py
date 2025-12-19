from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
import os, json, csv, shutil

from app.database import get_db, DB_PATH, DATA_DIR
from app.models import ExchangeRate, NewsArticle

router = APIRouter()

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

@router.post("/backup")
def backup_db(
    format: str = Query("all", pattern="^(all|sqlite|json|csv)$"),
    db: Session = Depends(get_db),
):
    """
    백업 API:
    - POST /backup?format=all|sqlite|json|csv
    - data/backups/YYYY-MM-DD/HHMMSS/ 아래에 생성
      - sqlite: app.db 복사
      - json: exchange.json, news.json
      - csv: exchange.csv, news.csv
    """
    now = datetime.now()
    day_dir = os.path.join(DATA_DIR, "backups", now.strftime("%Y-%m-%d"), now.strftime("%H%M%S"))
    ensure_dir(day_dir)

    outputs = []

    def dump_json():
        ex = db.execute(select(ExchangeRate).order_by(ExchangeRate.day.asc())).scalars().all()
        nw = db.execute(select(NewsArticle).order_by(NewsArticle.created_at.desc())).scalars().all()

        ex_path = os.path.join(day_dir, "exchange.json")
        news_path = os.path.join(day_dir, "news.json")

        with open(ex_path, "w", encoding="utf-8") as f:
            json.dump(
                [{"day": r.day.isoformat(), "currency": r.currency, "krw_per_unit": r.krw_per_unit} for r in ex],
                f, ensure_ascii=False, indent=2
            )
        with open(news_path, "w", encoding="utf-8") as f:
            json.dump(
                [{"title": r.title, "url": r.url, "domain": r.domain, "seendate": r.seendate, "created_at": r.created_at.isoformat()} for r in nw],
                f, ensure_ascii=False, indent=2
            )
        outputs.extend([ex_path, news_path])

    def dump_csv():
        ex = db.execute(select(ExchangeRate).order_by(ExchangeRate.day.asc())).scalars().all()
        nw = db.execute(select(NewsArticle).order_by(NewsArticle.created_at.desc())).scalars().all()

        ex_path = os.path.join(day_dir, "exchange.csv")
        news_path = os.path.join(day_dir, "news.csv")

        with open(ex_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["day", "currency", "krw_per_unit"])
            for r in ex:
                w.writerow([r.day.isoformat(), r.currency, r.krw_per_unit])

        with open(news_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["title", "url", "domain", "seendate", "created_at"])
            for r in nw:
                w.writerow([r.title, r.url, r.domain, r.seendate, r.created_at.isoformat()])

        outputs.extend([ex_path, news_path])

    def dump_sqlite():
        if not os.path.exists(DB_PATH):
            raise HTTPException(status_code=500, detail=f"DB file not found: {DB_PATH}")
        dst = os.path.join(day_dir, os.path.basename(DB_PATH))
        shutil.copy2(DB_PATH, dst)
        outputs.append(dst)

    if format in ("all", "sqlite"):
        dump_sqlite()
    if format in ("all", "json"):
        dump_json()
    if format in ("all", "csv"):
        dump_csv()

    return {"backup_dir": day_dir, "files": outputs}
