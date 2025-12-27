from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_  
from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)


@router.get("/", response_model=List[schemas.ActivityOut])
def list_activities(
    due_from: Optional[datetime] = None,
    due_to: Optional[datetime] = None,
    owner_user_id: Optional[int] = None,
    deal_id: Optional[int] = None,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.Activity)
        .outerjoin(models.Contact)
        .outerjoin(models.Deal)
        .outerjoin(models.Company)
    )

    if deal_id:
        query = query.filter(models.Activity.deal_id == deal_id)
    if owner_user_id:
        query = query.filter(models.Activity.owner_user_id == owner_user_id)
    if due_from:
        query = query.filter(models.Activity.due_date >= due_from)
    if due_to:
        query = query.filter(models.Activity.due_date <= due_to)
    if type:
        query = query.filter(models.Activity.type == type)

    results = (
        query
        .order_by(models.Activity.due_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Enriquecer resultados
    enriched = []
    for a in results:
        contact_name = (
            f"{a.contact.first_name} {a.contact.last_name}"
            if a.contact else None
        )
        deal_title = a.deal.title if a.deal else None
        company_name = a.deal.company.name if a.deal and a.deal.company else None

        enriched.append(
            schemas.ActivityOut(
                id=a.id,
                type=a.type,
                subject=a.subject,
                notes=a.notes,
                due_date=a.due_date,
                done=a.done,
                deal_id=a.deal_id,
                contact_id=a.contact_id,
                owner_user_id=a.owner_user_id,
                created_at=a.created_at,
                contact_name=contact_name,
                deal_title=deal_title,
                company_name=company_name,
            )
        )

    return enriched



@router.get("/{activity_id}", response_model=schemas.ActivityOut)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = (
        db.query(models.Activity)
        .filter(models.Activity.id == activity_id)
        .first()
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )
    return activity


@router.post("/", response_model=schemas.ActivityOut, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_in: schemas.ActivityCreate,
    db: Session = Depends(get_db),
):
    if activity_in.type not in ["call", "email", "meeting", "task"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activity type",
        )

    activity = models.Activity(**activity_in.dict())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.patch("/{activity_id}", response_model=schemas.ActivityOut)
def update_activity(
    activity_id: int,
    activity_in: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
):
    activity = (
        db.query(models.Activity)
        .filter(models.Activity.id == activity_id)
        .first()
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )

    data = activity_in.dict(exclude_unset=True)
    if "type" in data and data["type"] not in ["call", "email", "meeting", "task"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activity type",
        )

    for field, value in data.items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = (
        db.query(models.Activity)
        .filter(models.Activity.id == activity_id)
        .first()
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )

    db.delete(activity)
    db.commit()
    return None
