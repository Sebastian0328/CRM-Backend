from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/summary", response_model=schemas.DashboardSummary)
def get_dashboard_summary(
    owner_user_id: Optional[int] = None,
    days_ahead: int = 7,
    db: Session = Depends(get_db),
):
    """
    Resumen de pipeline + actividades próximas.
    - owner_user_id: filtra por comercial (opcional)
    - days_ahead: rango de días para actividades próximas
    """
    # ---------- DEALS POR ETAPA ----------
    deals_query = db.query(
        models.Deal.stage.label("stage"),
        func.count(models.Deal.id).label("count"),
        func.coalesce(func.sum(models.Deal.amount), 0).label("total_amount"),
    )

    if owner_user_id:
        deals_query = deals_query.filter(models.Deal.owner_user_id == owner_user_id)

    deals_query = deals_query.group_by(models.Deal.stage)

    deals_by_stage_rows = deals_query.all()

    deals_by_stage: List[schemas.DealStageStats] = [
        schemas.DealStageStats(
            stage=row.stage,
            count=row.count,
            total_amount=float(row.total_amount or 0),
        )
        for row in deals_by_stage_rows
    ]

    total_pipeline_value = float(
        sum(d.total_amount for d in deals_by_stage)
    )

    # --------- VALOR ESPERADO DEL PIPELINE ---------
    stage_prob = {
        "prospecting": 0.2,
        "qualified": 0.4,
        "proposal": 0.7,
        "won": 1.0,
        "lost": 0.0,
    }

    expected_pipeline_value = 0.0
    for d in deals_by_stage:
        prob = stage_prob.get(d.stage, 0.0)
        expected_pipeline_value += d.total_amount * prob

    # ---------- ACTIVIDADES PRÓXIMAS ----------
    now = datetime.utcnow()
    limit_date = now + timedelta(days=days_ahead)

    activities_query = (
        db.query(models.Activity)
        .options(
            joinedload(models.Activity.deal).joinedload(models.Deal.company),
            joinedload(models.Activity.contact),
        )
        .filter(models.Activity.due_date != None)
        .filter(models.Activity.due_date >= now)
        .filter(models.Activity.due_date <= limit_date)
        .order_by(models.Activity.due_date.asc())
    )

    if owner_user_id:
        activities_query = activities_query.filter(
            models.Activity.owner_user_id == owner_user_id
        )

    activities_rows = activities_query.all()

    upcoming_activities: List[schemas.UpcomingActivity] = []
    for act in activities_rows:
        company_id = act.deal.company_id if act.deal and act.deal.company_id else None
        contact_name = None
        if act.contact:
            contact_name = f"{act.contact.first_name} {act.contact.last_name}"

        upcoming_activities.append(
            schemas.UpcomingActivity(
                id=act.id,
                type=act.type,
                subject=act.subject,
                due_date=act.due_date,
                deal_id=act.deal_id,
                contact_id=act.contact_id,
                company_id=company_id,
                contact_name=contact_name,
            )
        )

    return schemas.DashboardSummary(
        deals_by_stage=deals_by_stage,
        total_pipeline_value=total_pipeline_value,
        expected_pipeline_value=expected_pipeline_value,   # ⬅️ NUEVO
        upcoming_activities=upcoming_activities,
    )
