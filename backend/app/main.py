import json
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, SessionLocal, engine, get_db
from .llm import AIGenerationError, generate_summary_and_tags

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Content Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_entry_out(entry: models.Entry) -> schemas.EntryOut:
    return schemas.EntryOut(
        id=entry.id,
        original_text=entry.original_text,
        summary=entry.summary,
        tags=json.loads(entry.tags) if entry.tags else [],
        status=entry.status,
        error_message=entry.error_message,
        created_at=entry.created_at,
    )


@app.post("/entries", response_model=schemas.EntryOut, status_code=201)
def create_entry(payload: schemas.EntryCreate, db: Session = Depends(get_db)):
    try:
        ai_output = generate_summary_and_tags(payload.text)
    except AIGenerationError as exc:
        entry = models.Entry(
            original_text=payload.text,
            status="failed",
            error_message=str(exc),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    entry = models.Entry(
        original_text=payload.text,
        summary=ai_output.summary,
        tags=json.dumps(ai_output.tags),
        status="completed",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _to_entry_out(entry)


@app.get("/entries", response_model=list[schemas.EntryOut])
def list_entries(tag: str | None = None, db: Session = Depends(get_db)):
    entries = db.query(models.Entry).order_by(models.Entry.created_at.desc()).all()
    results = [_to_entry_out(e) for e in entries]
    if tag:
        results = [e for e in results if tag in e.tags]
    return results


@app.get("/entries/{entry_id}", response_model=schemas.EntryOut)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return _to_entry_out(entry)
