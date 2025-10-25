from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import Settings, settings
from app.models import TokenData
from app.database import supabase

@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance to avoid reading the environment variables on every call
    """
    return Settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        account_id: str = payload.get("sub")
        
        if account_id is None:
            raise credentials_exception
            
        token_data = TokenData(account_id=account_id)
        
    except JWTError:
        raise credentials_exception
    
    # Note: Token validation is sufficient for most use cases.
    # Additional DB checks can be added here if needed for revoked tokens.
    
    return token_data.account_id