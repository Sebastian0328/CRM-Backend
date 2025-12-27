from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload  # 👈 joinedload añadido

from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/deals",
    tags=["deals"],
)


@router.get("/", response_model=List[schemas.DealOut])
def list_deals(
    stage: Optional[str] = None,
    company_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    owner_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Deal)

    if stage:
        query = query.filter(models.Deal.stage == stage)

    if company_id:
        query = query.filter(models.Deal.company_id == company_id)

    if owner_user_id:
        query = query.filter(models.Deal.owner_user_id == owner_user_id)

    deals_orm = (
        query
        .options(
            joinedload(models.Deal.company),
            joinedload(models.Deal.contact),
        )
        .order_by(models.Deal.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # devolvemos DealOut enriquecido con nombres de company/contact
    return [
        schemas.DealOut(
            id=d.id,
            title=d.title,
            amount=float(d.amount or 0),
            currency=d.currency,
            stage=d.stage,
            close_date=d.close_date,
            company_id=d.company_id,
            contact_id=d.contact_id,
            owner_user_id=d.owner_user_id,
            company_name=d.company.name if d.company else None,
            contact_name=(
                f"{d.contact.first_name} {d.contact.last_name}"
                if d.contact
                else None
            ),
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in deals_orm
    ]


@router.get("/{deal_id}", response_model=schemas.DealOut)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    d = (
        db.query(models.Deal)
        .options(
            joinedload(models.Deal.company),
            joinedload(models.Deal.contact),
        )
        .filter(models.Deal.id == deal_id)
        .first()
    )
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    return schemas.DealOut(
        id=d.id,
        title=d.title,
        amount=float(d.amount or 0),
        currency=d.currency,
        stage=d.stage,
        close_date=d.close_date,
        company_id=d.company_id,
        contact_id=d.contact_id,
        owner_user_id=d.owner_user_id,
        company_name=d.company.name if d.company else None,
        contact_name=(
            f"{d.contact.first_name} {d.contact.last_name}"
            if d.contact
            else None
        ),
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


@router.post("/", response_model=schemas.DealOut, status_code=status.HTTP_201_CREATED)
def create_deal(
    deal_in: schemas.DealCreate,
    db: Session = Depends(get_db),
):
    deal = models.Deal(**deal_in.dict())
    db.add(deal)
    db.commit()
    db.refresh(deal)
    # reutilizamos get_deal para devolverlo enriquecido con nombres
    return get_deal(deal.id, db)


@router.patch("/{deal_id}", response_model=schemas.DealOut)
def update_deal(
    deal_id: int,
    deal_in: schemas.DealUpdate,
    db: Session = Depends(get_db),
):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    data = deal_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(deal, field, value)

    db.commit()
    db.refresh(deal)
    return get_deal(deal.id, db)


@router.patch("/{deal_id}/stage", response_model=schemas.DealOut)
def update_deal_stage(
    deal_id: int,
    stage: str,
    db: Session = Depends(get_db),
):
    if stage not in ["prospecting", "qualified", "proposal", "won", "lost"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stage",
        )

    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    deal.stage = stage
    db.commit()
    db.refresh(deal)
    return get_deal(deal.id, db)


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    db.delete(deal)
    db.commit()
    return None

@router.get("/{deal_id}/activities", response_model=List[schemas.ActivitySummary])
def get_deal_activities(
    deal_id: int,
    db: Session = Depends(get_db),
):
    """
    Devuelve las actividades ligadas a un deal concreto,
    ordenadas de la más reciente a la más antigua.
    """
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )

    query = (
        db.query(models.Activity)
        .outerjoin(models.Contact)
        .filter(models.Activity.deal_id == deal_id)
        .order_by(models.Activity.due_date.desc())
        .limit(30)
    )

    activities: list[schemas.ActivitySummary] = []
    for a in query:
        contact_name = None
        if a.contact:
            contact_name = f"{a.contact.first_name} {a.contact.last_name}"

        activities.append(
            schemas.ActivitySummary(
                id=a.id,
                type=a.type,
                subject=a.subject,
                due_date=a.due_date,
                contact_name=contact_name,
                deal_title=deal.title,
            )
        )

    return activities