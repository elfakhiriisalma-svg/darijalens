"""Historique des analyses et statistiques pour le tableau de bord."""

from collections import Counter
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import MAX_STORED_TEXT, Analysis, get_session
from app.schemas import (
    DailyCount,
    HistoryCreated,
    HistoryEntry,
    RecentAnalysis,
    StatsResponse,
)

router = APIRouter(tags=["historique"])

SENTIMENT_KEYS = ("positive", "negative", "uncertain")
OFFENSIVE_KEYS = ("offensive", "non_offensive")
SCRIPT_KEYS = ("arabic", "latin", "mixed", "unknown")
RECENT_LIMIT = 10


def _as_utc(moment: datetime) -> datetime:
    """SQLite rend des dates sans fuseau : on les considère comme UTC."""
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _counts(session: Session, column, keys: tuple[str, ...]) -> dict[str, int]:
    found = dict(session.execute(select(column, func.count()).group_by(column)).all())
    return {key: int(found.get(key, 0)) for key in keys}


@router.post("/history", response_model=HistoryCreated, status_code=status.HTTP_201_CREATED)
def add_to_history(
    entry: HistoryEntry,
    session: Session = Depends(get_session),  # noqa: B008
) -> HistoryCreated:
    """Enregistre une analyse. Le texte est tronqué à 300 caractères."""
    row = Analysis(
        text=entry.text.strip()[:MAX_STORED_TEXT],
        script=entry.script,
        sentiment=entry.sentiment,
        sentiment_score=entry.sentiment_score,
        offensive=entry.offensive,
        offensive_score=entry.offensive_score,
    )
    session.add(row)
    session.commit()
    return HistoryCreated(id=row.id)


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(session: Session = Depends(get_session)) -> Response:  # noqa: B008
    """Efface tout l'historique."""
    session.execute(delete(Analysis))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stats", response_model=StatsResponse)
def stats(
    days: int = Query(default=14, ge=1, le=90, description="Nombre de jours pour la courbe."),
    session: Session = Depends(get_session),  # noqa: B008
) -> StatsResponse:
    """Totaux par sentiment, par langage offensant et par écriture, activité par jour, récents."""
    today = datetime.now(UTC).date()
    first_day = today - timedelta(days=days - 1)
    window_start = datetime.combine(first_day, datetime.min.time(), tzinfo=UTC)

    moments = session.scalars(
        select(Analysis.created_at).where(Analysis.created_at >= window_start)
    )
    per_day = Counter(_as_utc(moment).date() for moment in moments)
    daily = [
        DailyCount(date=(day := first_day + timedelta(days=offset)).isoformat(), count=per_day[day])
        for offset in range(days)
    ]

    recent_rows = session.scalars(
        select(Analysis)
        .order_by(Analysis.created_at.desc(), Analysis.id.desc())
        .limit(RECENT_LIMIT)
    ).all()
    return StatsResponse(
        total=session.scalar(select(func.count()).select_from(Analysis)) or 0,
        sentiment=_counts(session, Analysis.sentiment, SENTIMENT_KEYS),
        offensive=_counts(session, Analysis.offensive, OFFENSIVE_KEYS),
        scripts=_counts(session, Analysis.script, SCRIPT_KEYS),
        daily=daily,
        recent=[
            RecentAnalysis(
                id=row.id,
                created_at=_as_utc(row.created_at).isoformat(),
                text=row.text,
                script=row.script,
                sentiment=row.sentiment,
                offensive=row.offensive,
            )
            for row in recent_rows
        ],
    )
