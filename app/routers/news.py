from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import httpx

from app.database import get_db
from app.models import NewsArticle

router = APIRouter()

def fetch_gdelt_news(maxrecords: int, timespan: str) -> list[dict]:
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "economy OR inflation OR interest rate OR central bank OR GDP",
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(maxrecords),
        "sort": "HybridRel",
        "timespan": timespan,
    }
    with httpx.Client(timeout=20) as client:
        r = client.get(url, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="news upstream error")
        data = r.json()
    return data.get("articles") or []

@router.post("/refresh")
def refresh_news(maxrecords: int = 20, timespan: str = "1d", db: Session = Depends(get_db)):
    """
    업스트 저장 API:
    - GDELT에서 기사 리스트 가져와 DB 저장 (url unique)
    """
    if maxrecords < 1 or maxrecords > 100:
        raise HTTPException(status_code=400, detail="maxrecords must be between 1 and 100")

    articles = fetch_gdelt_news(maxrecords, timespan)

    saved = 0
    for a in articles:
        url = a.get("url")
        if not url:
            continue

        exists = db.execute(select(NewsArticle).where(NewsArticle.url == url)).scalar_one_or_none()
        if exists:
            continue

        db.add(NewsArticle(
            url=url,
            title=a.get("title"),
            domain=a.get("domain"),
            seendate=a.get("seendate"),
        ))
        saved += 1

    db.commit()
    return {"timespan": timespan, "fetched": len(articles), "saved_new": saved}

@router.get("")
def get_news(limit: int = 50, db: Session = Depends(get_db)):
    """
    조회 API:
    - DB에서 최신 기사부터 limit개 반환
    """
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")

    rows = db.execute(
        select(NewsArticle).order_by(NewsArticle.created_at.desc()).limit(limit)
    ).scalars().all()

    return {
        "count": len(rows),
        "articles": [
            {"title": r.title, "url": r.url, "domain": r.domain, "seendate": r.seendate, "created_at": r.created_at.isoformat()}
            for r in rows
        ],
        "note": "DB에 저장된 값 기준",
    }
