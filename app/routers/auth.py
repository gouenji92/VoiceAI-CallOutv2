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
    # Bcrypt chỉ hỗ trợ mật khẩu tối đa 72 bytes
    # Cắt theo BYTES, không phải ký tự
    print(f"[DEBUG] Mật khẩu nhận được: '{password}' (độ dài: {len(password)} ký tự, {len(password.encode('utf-8'))} bytes)")
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Cắt theo bytes và decode lại, xử lý ký tự bị cắt giữa chừng
        password = password_bytes[:72].decode('utf-8', errors='ignore')
        print(f"[DEBUG] Đã cắt xuống: '{password}' ({len(password.encode('utf-8'))} bytes)")
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    # Cắt ngắn mật khẩu giống như khi hash
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta # Đã sửa lỗi
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    response = supabase.table("accounts").select("id, password_hash").eq("email", form_data.username).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    user = response.data[0]
    
    # Kiểm tra mật khẩu
    if not verify_password(form_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user['id'])}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    try:
        # Kiểm tra email đã tồn tại chưa
        response = supabase.table("accounts").select("id").eq("email", user_in.email).execute()
        if response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email đã được đăng ký",
            )
            
        # Hash mật khẩu
        hashed_password = get_password_hash(user_in.password)
        
        # Tạo dữ liệu user mới
        new_user = {
            "email": user_in.email,
            "password_hash": hashed_password,
            "role": user_in.role
        }
        
        print(f"[DEBUG] Đang insert user: {user_in.email}")
        
        # Insert vào database
        insert_response = supabase.table("accounts").insert(new_user).execute()
        
        # Kiểm tra lỗi từ Supabase
        if hasattr(insert_response, 'error') and insert_response.error:
            print(f"[LỖI ĐĂNG KÝ] Full error object: {insert_response.error}")
            print(f"[LỖI ĐĂNG KÝ] Error type: {type(insert_response.error)}")
            error_detail = getattr(insert_response.error, 'message', str(insert_response.error))
            raise HTTPException(status_code=500, detail=f"Lỗi Supabase: {error_detail}")
        
        # Kiểm tra có data trả về không
        if not insert_response.data:
            raise HTTPException(status_code=500, detail="Không nhận được dữ liệu từ Supabase sau khi insert")
            
        print(f"[THÀNH CÔNG] Đã tạo tài khoản: {user_in.email}")
        return {"message": "Tạo tài khoản thành công", "email": user_in.email}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LỖI BẤT NGỜ] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi không xác định: {str(e)}")