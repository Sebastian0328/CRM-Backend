from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel


# ESTA PARTE ES PARA CREAR EL MODELO AL MOMENTO DE LLAMAR LA BASE DE DATOS, SE NECESITA QUE SEA IGUAL CON LOS MISMOS PARAMETROS Y TIPOS DE DATOS.

# --------- COMPANIES ---------
class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    owner_user_id: Optional[int] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    owner_user_id: Optional[int] = None


class CompanyOut(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# --------- CONTACTS ---------
class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    tags: Optional[dict] = None   # JSON


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    company_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    tags: Optional[dict] = None


class ContactOut(ContactBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# --------- DEALS ---------
class DealBase(BaseModel):
    title: str
    amount: float = 0
    currency: str = "EUR"
    stage: str = "prospecting"  # prospecting, qualified, proposal, won, lost
    close_date: Optional[date] = None
    company_id: int
    contact_id: Optional[int] = None
    owner_user_id: Optional[int] = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    stage: Optional[str] = None
    close_date: Optional[date] = None
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    owner_user_id: Optional[int] = None


class DealOut(DealBase):
    id: int
    created_at: datetime
    updated_at: datetime
    company_name: Optional[str] = None
    contact_name: Optional[str] = None

    class Config:
        orm_mode = True

# --------- ACTIVITIES ---------
class ActivityBase(BaseModel):
    type: str  # call, email, meeting, task
    subject: str
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    done: bool = False
    deal_id: Optional[int] = None
    contact_id: Optional[int] = None
    owner_user_id: Optional[int] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    subject: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    done: Optional[bool] = None
    deal_id: Optional[int] = None
    contact_id: Optional[int] = None
    owner_user_id: Optional[int] = None


class ActivityOut(BaseModel):
    id: int
    type: str
    subject: str
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    done: bool
    deal_id: Optional[int]
    contact_id: Optional[int]
    owner_user_id: Optional[int]
    created_at: datetime

    # 👇 NUEVOS CAMPOS
    contact_name: Optional[str] = None
    deal_title: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        orm_mode = True


# --------- DASHBOARD ---------
class DealStageStats(BaseModel):
    stage: str
    count: int
    total_amount: float


class UpcomingActivity(BaseModel):
    id: int
    type: str
    subject: str
    due_date: Optional[datetime]
    deal_id: Optional[int]
    contact_id: Optional[int]
    company_id: Optional[int] = None  # lo calcularemos vía join opcional
    contact_name: Optional[str] = None

    class Config:
        orm_mode = True


class DashboardSummary(BaseModel):
    deals_by_stage: List[DealStageStats]
    total_pipeline_value: float
    expected_pipeline_value: float   
    upcoming_activities: List[UpcomingActivity]

class ContactSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        orm_mode = True


class DealSummary(BaseModel):
    id: int
    title: str
    stage: str
    amount: float
    close_date: Optional[date] = None

    class Config:
        orm_mode = True



class ActivitySummary(BaseModel):
    id: int
    type: str
    subject: str
    due_date: Optional[datetime] = None
    contact_name: Optional[str] = None
    deal_title: Optional[str] = None

    class Config:
        orm_mode = True


# ---------- DETALLE DE COMPAÑÍA ----------
class CompanyDetail(BaseModel):
    id: int
    name: str
    industry: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    contacts: List[ContactSummary]
    deals: List[DealSummary]
    activities: List[ActivitySummary]

    class Config:
        orm_mode = True


# ---------- DETALLE DE CONTACTO ----------
class ContactDetail(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None

    company_id: Optional[int] = None
    company_name: Optional[str] = None
    company_industry: Optional[str] = None

    deals: List[DealSummary]
    activities: List[ActivitySummary]

    class Config:
        orm_mode = True

# ---------- DETALLE DE NEGOCIO ----------
class DealDetail(BaseModel):
    id: int
    title: str
    amount: float
    currency: str
    stage: str
    close_date: Optional[date]

    company_id: int
    company_name: Optional[str]
    company_city: Optional[str]
    company_country: Optional[str]

    contact_id: Optional[int]
    contact_name: Optional[str]

    activities: List[ActivitySummary]

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True