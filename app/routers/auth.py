from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import supabase
from app.models import Token, UserCreate
from app.config import settings
from jose import jwt
from datetime import datetime, timedelta, timezone # Đã import timezone
from passlib.context import CryptContext

router = APIRouter() 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta # Đã sửa lỗi
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

@router.post("/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    response = supabase.table("accounts").select("id, password_hash").eq("email", form_data.username).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    user = response.data[0]
    
    # BỎ COMMENT (BẬT LẠI) KHI BẠN ĐÃ HASH MẬT KHẨU
    # if not verify_password(form_data.password, user['password_hash']):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect email or password",
    #     )
    
    print(f"User {user['id']} dang nhap thanh cong (bo qua check hash)")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user['id'])}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register_user(user_in: UserCreate):
    response = supabase.table("accounts").select("id").eq("email", user_in.email).execute()
    if response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
        
    hashed_password = get_password_hash(user_in.password)
    
    new_user = {
        "email": user_in.email,
        "password_hash": hashed_password,
        "role": user_in.role
    }
    
    insert_response = supabase.table("accounts").insert(new_user).execute()
    
    if insert_response.error:
        raise HTTPException(status_code=500, detail=insert_response.error.message)
        
    return {"message": "Account created successfully", "email": user_in.email}