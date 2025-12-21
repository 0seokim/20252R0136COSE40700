from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import httpx

from app.database import get_db
from app.models import NewsArticle

router = APIRouter()

TRUSTED_DOMAINS = {
    # US / Global major business
    # "reuters.com",
    # "bloomberg.com",
    # "wsj.com",
    # "ft.com",
    # "nytimes.com",
    # "washingtonpost.com",
    "cnbc.com",
    # "finance.yahoo.com",
    # "marketwatch.com",
    # "theeconomist.com",

    # Korea major
    "yna.co.kr",
    "mk.co.kr",
    "hankyung.com",
    "sedaily.com",
    "biz.chosun.com",
}

# 한국/미국 판정(가능하면 sourceCountry 사용)
ALLOWED_SOURCE_COUNTRIES = {"US", "USA", "KR", "KOR"}

def is_allowed_country(a: dict) -> bool:
    sc = (a.get("sourceCountry") or "").upper()
    if sc in ALLOWED_SOURCE_COUNTRIES:
        return True
    # sourceCountry가 비거나 애매한 경우를 위한 보완(제목 기반 약식)
    title = (a.get("title") or "").lower()
    return ("korea" in title) or ("south korea" in title) or ("u.s." in title) or ("united states" in title)

def is_trusted_domain(a: dict) -> bool:
    d = (a.get("domain") or "").lower().strip()
    return d in TRUSTED_DOMAINS

def fetch_gdelt_raw(maxrecords: int, timespan: str) -> list[dict]:
    url = "https://api.gdeltproject.org/api/v2/doc/doc"

    # ✅ 쿼리를 짧게 유지 (OR 묶음만)
    query = '(economy OR inflation OR "interest rate" OR "central bank" OR GDP)'

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(maxrecords),
        "sort": "HybridRel",
        "timespan": timespan,
    }

    with httpx.Client(timeout=25) as client:
        r = client.get(url, params=params)

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"GDELT upstream status={r.status_code}, body={r.text[:500]}")

    try:
        data = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail=f"GDELT returned non-JSON: {r.text[:500]}")

    return data.get("articles") or []


@router.post("/refresh")
def refresh_news(maxrecords: int = 20, timespan: str = "1d", db: Session = Depends(get_db)):
    """
    - GDELT에서 넉넉히 가져온 뒤
    - (한국/미국) + (유명 도메인)으로 서버에서 필터링
    - 최종 maxrecords개만 DB 저장(url unique)
    """
    if maxrecords < 1 or maxrecords > 100:
        raise HTTPException(status_code=400, detail="maxrecords must be between 1 and 100")

    # ✅ 원본은 넉넉히 가져오기 (필터 후 maxrecords 채우기 위해)
    raw = fetch_gdelt_raw(maxrecords=250, timespan=timespan)

    filtered = []
    for a in raw:
        if is_trusted_domain(a) and is_allowed_country(a):
            filtered.append(a)
        if len(filtered) >= maxrecords:
            break

    saved = 0
    for a in filtered:
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
    return {
        "timespan": timespan,
        "fetched_raw": len(raw),
        "filtered": len(filtered),
        "saved_new": saved,
        "trusted_domains": sorted(list(TRUSTED_DOMAINS)),
        "country_rule": "sourceCountry in {KR,US} else title contains Korea/US keywords (fallback)",
    }


@router.get("")
def get_news(limit: int = 50, db: Session = Depends(get_db)):
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
        "note": "DB에 저장된 값 기준 (서버 필터 적용)",
    }
