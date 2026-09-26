from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import User, DiagnosticCentre, DiagnosticTest, Booking, Payment
from .schemas import *
from .security import hash_password, verify_password, create_token, current_user

app=FastAPI(title='EVE Healthcare Diagnostic Booking API', version='1.0.0')
Base.metadata.create_all(bind=engine)

def page_params(page:int=Query(1,ge=1), size:int=Query(20,ge=1,le=100)): return page,size

@app.post('/auth/signup/', response_model=TokenResponse, status_code=201)
def signup(payload:SignupRequest, db:Session=Depends(get_db)):
    email=payload.email.lower()
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,'Email already registered')
    u=User(email=email,password_hash=hash_password(payload.password)); db.add(u); db.commit(); db.refresh(u)
    return {'access_token':create_token(u.id)}

@app.post('/auth/login/', response_model=TokenResponse)
def login(payload:SignupRequest, db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==payload.email.lower()))
    if not u or not verify_password(payload.password,u.password_hash): raise HTTPException(401,'Invalid email or password')
    return {'access_token':create_token(u.id)}

@app.post('/centres/', response_model=CentreOut, status_code=201)
def create_centre(payload:CentreCreate, _:User=Depends(current_user), db:Session=Depends(get_db)):
    c=DiagnosticCentre(**payload.model_dump()); db.add(c); db.commit(); db.refresh(c); return c

@app.get('/centres/', response_model=list[CentreOut])
def list_centres(page_size=Depends(page_params), db:Session=Depends(get_db)):
    page,size=page_size; return db.scalars(select(DiagnosticCentre).order_by(DiagnosticCentre.id).offset((page-1)*size).limit(size)).all()

@app.get('/centres/{centre_id}', response_model=CentreOut)
def get_centre(centre_id:int, db:Session=Depends(get_db)):
    c=db.get(DiagnosticCentre,centre_id)
    if not c: raise HTTPException(404,'Centre not found')
    return c

@app.post('/tests/', response_model=TestOut, status_code=201)
def create_test(payload:TestCreate, _:User=Depends(current_user), db:Session=Depends(get_db)):
    if not db.get(DiagnosticCentre,payload.centre_id): raise HTTPException(404,'Centre not found')
    t=DiagnosticTest(**payload.model_dump()); db.add(t); db.commit(); db.refresh(t); return t

@app.get('/tests/', response_model=list[TestOut])
def list_tests(centre_id:int|None=None, page_size=Depends(page_params), db:Session=Depends(get_db)):
    page,size=page_size; q=select(DiagnosticTest).order_by(DiagnosticTest.id)
    if centre_id: q=q.where(DiagnosticTest.centre_id==centre_id)
    return db.scalars(q.offset((page-1)*size).limit(size)).all()

@app.post('/bookings/', response_model=BookingOut, status_code=201)
def create_booking(payload:BookingCreate, user:User=Depends(current_user), db:Session=Depends(get_db)):
    if payload.appointment_at <= datetime.now(timezone.utc): raise HTTPException(400,'Appointment must be in the future')
    c=db.get(DiagnosticCentre,payload.centre_id); t=db.get(DiagnosticTest,payload.test_id)
    if not c or not t: raise HTTPException(404,'Centre or test not found')
    if t.centre_id != c.id: raise HTTPException(400,'Test is not offered by selected centre')
    b=Booking(user_id=user.id,test_id=t.id,centre_id=c.id,appointment_at=payload.appointment_at,amount=t.price,status='PENDING')
    db.add(b); db.commit(); db.refresh(b); return b

@app.get('/bookings/', response_model=list[BookingOut])
def list_bookings(user:User=Depends(current_user), page_size=Depends(page_params), db:Session=Depends(get_db)):
    page,size=page_size; return db.scalars(select(Booking).where(Booking.user_id==user.id).order_by(Booking.id.desc()).offset((page-1)*size).limit(size)).all()

@app.get('/bookings/{booking_id}', response_model=BookingOut)
def get_booking(booking_id:int, user:User=Depends(current_user), db:Session=Depends(get_db)):
    b=db.get(Booking,booking_id)
    if not b: raise HTTPException(404,'Booking not found')
    if b.user_id!=user.id: raise HTTPException(403,'Not authorized to access this booking')
    return b

@app.post('/payments/', response_model=PaymentOut, status_code=201)
def payment(payload:PaymentRequest, user:User=Depends(current_user), db:Session=Depends(get_db)):
    b=db.get(Booking,payload.booking_id)
    if not b: raise HTTPException(404,'Booking not found')
    if b.user_id!=user.id: raise HTTPException(403,'Not authorized')
    if b.payment: return b.payment
    if b.status not in ('PENDING','FAILED'): raise HTTPException(400,'Booking cannot be paid in its current state')
    result=payload.force_status.upper()
    if result not in ('SUCCESS','FAILED'): raise HTTPException(422,'force_status must be SUCCESS or FAILED')
    pid=payload.provider_payment_id or f'mock-{b.id}-{int(datetime.now().timestamp()*1000)}'
    existing=db.scalar(select(Payment).where(Payment.provider_payment_id==pid))
    if existing: return existing
    p=Payment(booking_id=b.id,provider_payment_id=pid,status=result); b.status='CONFIRMED' if result=='SUCCESS' else 'FAILED'; db.add(p); db.commit(); db.refresh(p); return p

@app.post('/payments/webhook/', response_model=PaymentOut)
def webhook(payload:WebhookRequest, db:Session=Depends(get_db)):
    existing=db.scalar(select(Payment).where(Payment.event_id==payload.event_id))
    if existing: return existing
    b=db.get(Booking,payload.booking_id)
    if not b: raise HTTPException(404,'Booking not found')
    status_value=payload.status.upper()
    if status_value not in ('SUCCESS','FAILED'): raise HTTPException(422,'status must be SUCCESS or FAILED')
    existing_payment=db.scalar(select(Payment).where(Payment.provider_payment_id==payload.payment_id))
    if existing_payment:
        if existing_payment.booking_id != b.id: raise HTTPException(409,'Payment ID belongs to another booking')
        existing_payment.event_id=payload.event_id; existing_payment.status=status_value
        b.status='CONFIRMED' if status_value=='SUCCESS' else 'FAILED'; db.commit(); return existing_payment
    p=Payment(booking_id=b.id,provider_payment_id=payload.payment_id,event_id=payload.event_id,status=status_value)
    b.status='CONFIRMED' if status_value=='SUCCESS' else 'FAILED'; db.add(p); db.commit(); db.refresh(p); return p
