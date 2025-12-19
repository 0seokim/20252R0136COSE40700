from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
import httpx

router = APIRouter()

def iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


@router.get("")
async def get_exchange(days: int = 14):
    """
    최근 N일(기본 14일)의 환율을 반환합니다.
    - usd_krw: 1 USD -> KRW
    - eur_krw: 1 EUR -> KRW
    - jpy_krw: 1 JPY -> KRW
    - jpy100_krw: 100 JPY -> KRW
    """
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
        "source": "frankfurter.dev",
    }
