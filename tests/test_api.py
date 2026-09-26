import os
os.environ['DATABASE_URL']='sqlite:///./test.db'
os.environ['JWT_SECRET']='test-secret'
from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app

Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
client=TestClient(app)

def auth(email='a@example.com'):
    r=client.post('/auth/signup/',json={'email':email,'password':'Password123'}); return {'Authorization':'Bearer '+r.json()['access_token']}

def test_booking_payment_webhook_idempotency():
    h=auth()
    c=client.post('/centres/',headers=h,json={'name':'City Diagnostics','location':'Noida'}).json()
    t=client.post('/tests/',headers=h,json={'name':'CBC','price':500,'centre_id':c['id']}).json()
    b=client.post('/bookings/',headers=h,json={'test_id':t['id'],'centre_id':c['id'],'appointment_at':'2027-01-01T10:00:00+05:30'}).json()
    p=client.post('/payments/webhook/',json={'event_id':'evt-1','payment_id':'pay-1','booking_id':b['id'],'status':'SUCCESS'}); assert p.status_code==200
    p2=client.post('/payments/webhook/',json={'event_id':'evt-1','payment_id':'pay-1','booking_id':b['id'],'status':'SUCCESS'}); assert p2.status_code==200
    assert client.get(f"/bookings/{b['id']}",headers=h).json()['status']=='CONFIRMED'

def test_unauthorized_booking():
    h=auth('b@example.com'); c=client.get('/centres/').json()[0]; t=client.get('/tests/').json()[0]
    b=client.post('/bookings/',headers=h,json={'test_id':t['id'],'centre_id':c['id'],'appointment_at':'2027-01-01T10:00:00+05:30'}).json()
    r=client.get(f"/bookings/{b['id']}",headers={'Authorization':'Bearer invalid'}); assert r.status_code==401
