from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class TokenResponse(BaseModel): access_token: str; token_type: str='bearer'
class CentreCreate(BaseModel): name: str=Field(min_length=2,max_length=150); location: str=Field(min_length=2,max_length=255)
class CentreOut(CentreCreate): model_config=ConfigDict(from_attributes=True); id:int
class TestCreate(BaseModel): name:str=Field(min_length=2,max_length=150); price:Decimal=Field(gt=0); centre_id:int=Field(gt=0)
class TestOut(TestCreate): model_config=ConfigDict(from_attributes=True); id:int
class BookingCreate(BaseModel): test_id:int=Field(gt=0); centre_id:int=Field(gt=0); appointment_at:datetime
class BookingOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; user_id:int; test_id:int; centre_id:int; appointment_at:datetime; amount:Decimal; status:str
class PaymentRequest(BaseModel):
    booking_id:int=Field(gt=0)
    force_status:str='SUCCESS'
    provider_payment_id:str|None=None

class WebhookRequest(BaseModel): event_id:str=Field(min_length=1,max_length=150); payment_id:str=Field(min_length=1,max_length=150); booking_id:int=Field(gt=0); status:str

class PaymentOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; booking_id:int; provider_payment_id:str; event_id:str|None; status:str
