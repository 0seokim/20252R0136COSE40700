from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter()

@router.get("")
async def get_news(maxrecords: int = 20, timespan: str = "1d"):
    """
    경제 뉴스 기사 리스트를 반환합니다.
    - 소스: GDELT DOC API
    - timespan 예: 1d, 12h, 3d ...
    """
    if maxrecords < 1 or maxrecords > 100:
        raise HTTPException(status_code=400, detail="maxrecords must be between 1 and 100")

    query = "economy OR inflation OR interest rate OR central bank OR GDP"

    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(maxrecords),
        "sort": "HybridRel",
        "timespan": timespan,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="news upstream error")

    data = r.json()
    articles = data.get("articles") or []

    cleaned = []
    for a in articles:
        cleaned.append({
            "title": a.get("title"),
            "url": a.get("url"),
            "domain": a.get("domain"),
            "language": a.get("language"),
            "sourceCountry": a.get("sourceCountry"),
            "seendate": a.get("seendate"),
        })

    return {
        "timespan": timespan,
        "count": len(cleaned),
        "articles": cleaned,
        "source": "gdelt",
    }
