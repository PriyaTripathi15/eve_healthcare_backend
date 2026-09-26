from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__='users'
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    bookings=relationship('Booking', back_populates='user')

class DiagnosticCentre(Base):
    __tablename__='diagnostic_centres'
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(150), index=True)
    location: Mapped[str]=mapped_column(String(255))
    tests=relationship('DiagnosticTest', back_populates='centre', cascade='all, delete-orphan')

class DiagnosticTest(Base):
    __tablename__='diagnostic_tests'
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(150), index=True)
    price: Mapped[Decimal]=mapped_column(Numeric(10,2))
    centre_id: Mapped[int]=mapped_column(ForeignKey('diagnostic_centres.id', ondelete='CASCADE'))
    centre=relationship('DiagnosticCentre', back_populates='tests')
    bookings=relationship('Booking', back_populates='test')

class Booking(Base):
    __tablename__='bookings'
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey('users.id'))
    test_id: Mapped[int]=mapped_column(ForeignKey('diagnostic_tests.id'))
    centre_id: Mapped[int]=mapped_column(ForeignKey('diagnostic_centres.id'))
    appointment_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    amount: Mapped[Decimal]=mapped_column(Numeric(10,2))
    status: Mapped[str]=mapped_column(String(20), default='PENDING', index=True)
    user=relationship('User', back_populates='bookings')
    test=relationship('DiagnosticTest', back_populates='bookings')
    centre=relationship('DiagnosticCentre')
    payment=relationship('Payment', back_populates='booking', uselist=False, cascade='all, delete-orphan')

class Payment(Base):
    __tablename__='payments'
    __table_args__=(UniqueConstraint('provider_payment_id', name='uq_provider_payment_id'), UniqueConstraint('event_id', name='uq_event_id'))
    id: Mapped[int]=mapped_column(primary_key=True)
    booking_id: Mapped[int]=mapped_column(ForeignKey('bookings.id'), unique=True)
    provider_payment_id: Mapped[str]=mapped_column(String(150), unique=True)
    event_id: Mapped[str|None]=mapped_column(String(150), nullable=True)
    status: Mapped[str]=mapped_column(String(20))
    booking=relationship('Booking', back_populates='payment')
