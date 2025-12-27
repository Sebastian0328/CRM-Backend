from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
)

@router.get("/", response_model=List[schemas.CompanyOut])
def list_companies(
    search: Optional[str] = None,
    city: Optional[str] = None,
    industry: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(models.Company)

    if search:
        like = f"%{search}%"
        query = query.filter(models.Company.name.ilike(like))

    if city:
        query = query.filter(models.Company.city.ilike(f"%{city}%"))

    if industry:
        query = query.filter(models.Company.industry.ilike(f"%{industry}%"))

    return (
        query
        .order_by(models.Company.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

@router.get("/{company_id}", response_model=schemas.CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return company


@router.post("/", response_model=schemas.CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    company_in: schemas.CompanyCreate,
    db: Session = Depends(get_db),
):
    # Comprobar si el nombre ya existe
    existing = (
        db.query(models.Company)
        .filter(models.Company.name == company_in.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company with this name already exists",
        )

    company = models.Company(**company_in.dict())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.patch("/{company_id}", response_model=schemas.CompanyOut)
def update_company(
    company_id: int,
    company_in: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    data = company_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    db.delete(company)
    db.commit()
    return None

@router.get("/{company_id}/detail", response_model=schemas.CompanyDetail)
def get_company_detail(company_id: int, db: Session = Depends(get_db)):
    """
    Devuelve:
    - datos de la compañía
    - contactos relacionados
    - deals relacionados
    - actividades recientes ligadas a esa compañía
    """
    company = (
        db.query(models.Company)
        .options(
            joinedload(models.Company.contacts),
            joinedload(models.Company.deals),
        )
        .filter(models.Company.id == company_id)
        .first()
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # contactos
    contacts = [
        schemas.ContactSummary(
            id=c.id,
            first_name=c.first_name,
            last_name=c.last_name,
            job_title=c.position,
            email=c.email,
            phone=c.phone,
        )
        for c in getattr(company, "contacts", [])
    ]

    # deals
    deals = [
        schemas.DealSummary(
            id=d.id,
            title=d.title,
            stage=d.stage,
            amount=float(d.amount or 0),
            close_date=d.close_date,
        )
        for d in getattr(company, "deals", [])
    ]

    # actividades ligadas a esta compañía
    activities_query = (
    db.query(models.Activity)
    .outerjoin(models.Deal, models.Activity.deal_id == models.Deal.id)
    .outerjoin(models.Contact, models.Activity.contact_id == models.Contact.id)
    .filter(
        or_(
            models.Deal.company_id == company_id,
            models.Contact.company_id == company_id,
        )
    )
    .order_by(models.Activity.due_date.desc())
    .limit(20)
)
    activities: list[schemas.ActivitySummary] = []
    for a in activities_query:
        contact_name = None
        if a.contact:
            contact_name = f"{a.contact.first_name} {a.contact.last_name}"

        deal_title = a.deal.title if a.deal else None

        activities.append(
            schemas.ActivitySummary(
                id=a.id,
                type=a.type,
                subject=a.subject,
                due_date=a.due_date,
                contact_name=contact_name,
                deal_title=deal_title,
            )
        )

    return schemas.CompanyDetail(
        id=company.id,
        name=company.name,
        industry=company.industry,
        city=company.city,
        country=company.country,
        website=company.website,
        phone=company.phone,
        address=company.address,
        contacts=contacts,
        deals=deals,
        activities=activities,
    )