from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from sqlalchemy.orm import joinedload

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
)


@router.get("/", response_model=List[schemas.ContactOut])
def list_contacts(
    search: Optional[str] = None,
    company_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(models.Contact)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Contact.first_name.ilike(like)) |
            (models.Contact.last_name.ilike(like)) |
            (models.Contact.email.ilike(like))
        )

    if company_id:
        query = query.filter(models.Contact.company_id == company_id)

    # 👇 SIEMPRE se ejecuta, da igual los if anteriores
    contacts_orm = (
        query
        .options(joinedload(models.Contact.company))
        .order_by(models.Contact.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Construimos la respuesta incluyendo company_name
    return [
        schemas.ContactOut(
            id=c.id,
            first_name=c.first_name,
            last_name=c.last_name,
            email=c.email,
            phone=c.phone,
            position=c.position,
            company_id=c.company_id,
            company_name=c.company.name if c.company else None,
            owner_user_id=c.owner_user_id,
            tags=c.tags,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in contacts_orm
    ]

@router.get("/{contact_id}", response_model=schemas.ContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return contact
#---- ENDPOINT PARA DETALLE COMPLETO DEL CONTACTO ----#

@router.get("/{contact_id}/detail", response_model=schemas.ContactDetail)
def get_contact_detail(contact_id: int, db: Session = Depends(get_db)):
    contact = (
        db.query(models.Contact)
        .options(joinedload(models.Contact.company),
                 joinedload(models.Contact.deals))
        .filter(models.Contact.id == contact_id)
        .first()
    )
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    # deals del contacto
    deals = [
        schemas.DealSummary(
            id=d.id,
            title=d.title,
            stage=d.stage,
            amount=float(d.amount or 0),
            close_date=d.close_date,
        )
        for d in getattr(contact, "deals", [])
    ]

    # actividades ligadas al contacto
    activities_q = (
        db.query(models.Activity)
        .outerjoin(models.Deal, models.Activity.deal_id == models.Deal.id)
        .filter(models.Activity.contact_id == contact_id)
        .order_by(models.Activity.due_date.desc())
        .limit(20)
    )

    activities: list[schemas.ActivitySummary] = []
    for a in activities_q:
        deal_title = a.deal.title if a.deal else None
        activities.append(
            schemas.ActivitySummary(
                id=a.id,
                type=a.type,
                subject=a.subject,
                due_date=a.due_date,
                contact_name=f"{contact.first_name} {contact.last_name}",
                deal_title=deal_title,
            )
        )

    return schemas.ContactDetail(
        id=contact.id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone=contact.phone,
        position=contact.position,
        company_id=contact.company_id,
        company_name=contact.company.name if contact.company else None,
        company_industry=contact.company.industry if contact.company else None,
        deals=deals,
        activities=activities,
    )

@router.post("/", response_model=schemas.ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(contact_in: schemas.ContactCreate, db: Session = Depends(get_db)):
    if contact_in.email:
        existing = (
            db.query(models.Contact)
            .filter(models.Contact.email == contact_in.email)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact with this email already exists",
            )

    contact = models.Contact(**contact_in.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.patch("/{contact_id}", response_model=schemas.ContactOut)
def update_contact(
    contact_id: int,
    contact_in: schemas.ContactUpdate,
    db: Session = Depends(get_db),
):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    data = contact_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    db.delete(contact)
    db.commit()
    return None
