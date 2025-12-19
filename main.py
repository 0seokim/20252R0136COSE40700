from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import date, timedelta
import httpx

app = FastAPI(title="Economy Backend API", version="1.0.0")

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")


def iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/exchange")
async def exchange(days: int = 14):
    if days < 2 or days > 60:
        raise HTTPException(status_code=400, detail="days must be between 2 and 60")

    end = date.today()
    start = end - timedelta(days=days - 1)

    async def fetch_timeseries(base: str):
        url = f"https://api.frankfurter.dev/v1/{iso(start)}..{iso(end)}"
        params = {"base": base, "symbols": "KRW"}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            if r.status_code != 200:
                raise HTTPException(status_code=502, detail=f"exchange upstream error: {base}")
            return r.json()

    usd, eur, jpy = await fetch_timeseries("USD"), await fetch_timeseries("EUR"), await fetch_timeseries("JPY")

    dates = sorted(set(list((usd.get("rates") or {}).keys())
                      + list((eur.get("rates") or {}).keys())
                      + list((jpy.get("rates") or {}).keys())))

    rows = []
    for d in dates:
        usdkrw = (usd.get("rates") or {}).get(d, {}).get("KRW")
        eurkrw = (eur.get("rates") or {}).get(d, {}).get("KRW")
        jpykrw = (jpy.get("rates") or {}).get(d, {}).get("KRW")
        rows.append({
            "date": d,
            "usd_krw": usdkrw,
            "eur_krw": eurkrw,
            "jpy_krw": jpykrw,
            "jpy100_krw": (jpykrw * 100) if jpykrw is not None else None,
        })

    return {
        "range": {"start": iso(start), "end": iso(end)},
        "rows": rows,
        "note": "주말/휴일은 데이터가 없을 수 있습니다(영업일 기준).",
    }


@app.get("/news")
async def news(maxrecords: int = 20, timespan: str = "1d"):
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
            "seendate": a.get("seendate"),
        })

    return {"timespan": timespan, "count": len(cleaned), "articles": cleaned}
