from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date, timedelta, datetime
import httpx

from app.database import get_db
from app.models import ExchangeRate

router = APIRouter()

def iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def parse_day(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def fetch_frankfurter_timeseries(base: str, start: date, end: date) -> dict:
    url = f"https://api.frankfurter.dev/v1/{iso(start)}..{iso(end)}"
    params = {"base": base, "symbols": "KRW"}
    with httpx.Client(timeout=20) as client:
        r = client.get(url, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"exchange upstream error: {base}")
        return r.json()

def upsert_rate(db: Session, day: date, currency: str, krw: float):
    existing = db.execute(
        select(ExchangeRate).where(ExchangeRate.day == day, ExchangeRate.currency == currency)
    ).scalar_one_or_none()

    if existing:
        existing.krw_per_unit = krw
    else:
        db.add(ExchangeRate(day=day, currency=currency, krw_per_unit=krw))

@router.post("/refresh")
def refresh_exchange(days: int = 14, db: Session = Depends(get_db)):
    """
    업스트 저장 API:
    - Frankfurter에서 최근 N일 환율을 가져와 DB에 저장
    """
    if days < 2 or days > 60:
        raise HTTPException(status_code=400, detail="days must be between 2 and 60")

    end = date.today()
    start = end - timedelta(days=days - 1)

    usd = fetch_frankfurter_timeseries("USD", start, end)
    eur = fetch_frankfurter_timeseries("EUR", start, end)
    jpy = fetch_frankfurter_timeseries("JPY", start, end)

    # dates union
    dates = sorted(set(list((usd.get("rates") or {}).keys())
                      + list((eur.get("rates") or {}).keys())
                      + list((jpy.get("rates") or {}).keys())))

    saved = 0
    for ds in dates:
        d = parse_day(ds)
        u = (usd.get("rates") or {}).get(ds, {}).get("KRW")
        e = (eur.get("rates") or {}).get(ds, {}).get("KRW")
        j = (jpy.get("rates") or {}).get(ds, {}).get("KRW")

        if u is not None:
            upsert_rate(db, d, "USD", float(u)); saved += 1
        if e is not None:
            upsert_rate(db, d, "EUR", float(e)); saved += 1
        if j is not None:
            upsert_rate(db, d, "JPY", float(j)); saved += 1

    db.commit()
    return {"range": {"start": iso(start), "end": iso(end)}, "saved": saved}

@router.get("")
def get_exchange(days: int = 14, db: Session = Depends(get_db)):
    """
    조회 API:
    - DB에서 최근 N일 범위 데이터를 읽어 반환
    - 최신 날짜가 위로 오도록 내림차순 정렬
    """
    if days < 2 or days > 60:
        raise HTTPException(status_code=400, detail="days must be between 2 and 60")

    end = date.today()
    start = end - timedelta(days=days - 1)

    # ✅ 변경: day DESC로 정렬
    rows = db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.day.between(start, end))
        .order_by(ExchangeRate.day.desc())
    ).scalars().all()

    by_day = {}
    for r in rows:
        ds = iso(r.day)
        by_day.setdefault(ds, {})
        by_day[ds][r.currency] = r.krw_per_unit

    # ✅ 변경: 최신 날짜가 먼저 나오도록 ds도 DESC 정렬
    out = []
    for ds in sorted(by_day.keys(), reverse=True):
        u = by_day[ds].get("USD")
        e = by_day[ds].get("EUR")
        j = by_day[ds].get("JPY")
        out.append({
            "date": ds,
            "usd_krw": u,
            "eur_krw": e,
            "jpy_krw": j,
            "jpy100_krw": (j * 100) if j is not None else None,
        })

    return {
        "range": {"start": iso(start), "end": iso(end)},
        "rows": out,
        "note": "DB에 저장된 값 기준 (내림차순 정렬)",
    }
