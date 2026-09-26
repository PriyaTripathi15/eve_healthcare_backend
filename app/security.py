import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

pwd=CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth=OAuth2PasswordBearer(tokenUrl='/auth/login/')
SECRET=os.getenv('JWT_SECRET','dev-secret-change-me'); ALG=os.getenv('JWT_ALGORITHM','HS256')

def hash_password(p): return pwd.hash(p)
def verify_password(p,h): return pwd.verify(p,h)
def create_token(uid): return jwt.encode({'sub':str(uid),'exp':datetime.now(timezone.utc)+timedelta(minutes=int(os.getenv('ACCESS_TOKEN_MINUTES','60')))}, SECRET, algorithm=ALG)
def current_user(token:str=Depends(oauth), db:Session=Depends(get_db)):
    cred=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid authentication credentials', headers={'WWW-Authenticate':'Bearer'})
    try: uid=int(jwt.decode(token,SECRET,algorithms=[ALG])['sub'])
    except (JWTError,ValueError,KeyError): raise cred
    user=db.get(User,uid)
    if not user: raise cred
    return user
