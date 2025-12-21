from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from app.database import DATA_DIR

router = APIRouter(prefix="/notes", tags=["notes"])

NOTES_PATH = os.path.join(DATA_DIR, "notes.txt")

class NoteIn(BaseModel):
    text: str

@router.get("")
def load_notes():
    if not os.path.exists(NOTES_PATH):
        return {"text": ""}
    with open(NOTES_PATH, "r", encoding="utf-8") as f:
        return {"text": f.read()}

@router.post("")
def save_notes(payload: NoteIn):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(NOTES_PATH, "w", encoding="utf-8") as f:
        f.write(payload.text or "")
    return {"ok": True, "path": NOTES_PATH}
