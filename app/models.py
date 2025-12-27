from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Enum,
    TIMESTAMP,
    Text,
    Date,
    DateTime,
    DECIMAL,
    Boolean,
    ForeignKey,
    JSON,
    CHAR,
)
from sqlalchemy.sql import func     
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        Enum("admin", "seller", "viewer", name="role_enum"),
        nullable=False,
        default="seller",
    )
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    last_login = Column(TIMESTAMP, nullable=True)

    companies = relationship("Company", back_populates="owner")
    contacts = relationship("Contact", back_populates="owner")
    deals = relationship("Deal", back_populates="owner")
    activities = relationship("Activity", back_populates="owner")


class Company(Base):
    __tablename__ = "companies"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(180), nullable=False, unique=True, index=True)
    industry = Column(String(120), nullable=True)
    website = Column(String(200), nullable=True)
    phone = Column(String(40), nullable=True)
    country = Column(String(80), nullable=True)
    city = Column(String(80), nullable=True)
    address = Column(String(200), nullable=True)
    owner_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    owner = relationship("User", back_populates="companies")
    contacts = relationship("Contact", back_populates="company")
    deals = relationship("Deal", back_populates="company")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(160), unique=True, nullable=True, index=True)
    phone = Column(String(40), nullable=True)
    position = Column(String(120), nullable=True)
    company_id = Column(BigInteger, ForeignKey("companies.id"), nullable=True)
    owner_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    company = relationship("Company", back_populates="contacts")
    owner = relationship("User", back_populates="contacts")
    deals = relationship("Deal", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    currency = Column(CHAR(3), nullable=False, default="EUR")
    stage = Column(
        Enum(
            "prospecting",
            "qualified",
            "proposal",
            "won",
            "lost",
            name="deal_stage_enum",
        ),
        nullable=False,
        default="prospecting",
    )
    close_date = Column(Date, nullable=True)
    company_id = Column(BigInteger, ForeignKey("companies.id"), nullable=False)
    contact_id = Column(BigInteger, ForeignKey("contacts.id"), nullable=True)
    owner_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    company = relationship("Company", back_populates="deals")
    contact = relationship("Contact", back_populates="deals")
    owner = relationship("User", back_populates="deals")
    activities = relationship("Activity", back_populates="deal")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    type = Column(
        Enum("call", "email", "meeting", "task", name="activity_type_enum"),
        nullable=False,
    )
    subject = Column(String(200), nullable=False)
    notes = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    done = Column(Boolean, nullable=False, default=False)
    deal_id = Column(BigInteger, ForeignKey("deals.id"), nullable=True)
    contact_id = Column(BigInteger, ForeignKey("contacts.id"), nullable=True)
    owner_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )

    deal = relationship("Deal", back_populates="activities")
    contact = relationship("Contact", back_populates="activities")
    owner = relationship("User", back_populates="activities")
