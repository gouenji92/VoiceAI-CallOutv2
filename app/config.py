from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    JWT_SECRET_KEY: str = "VCskjRFh2NdkIrzDbw0P8HvKiO4h+ODsghkZ0r8OCXy2CjB0WWkBIJ/OWsDyMdEhbzrGjK/pMByL+mDnevslLg==" # Thay bằng key bí mật
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 ngày

    class Config:
        env_file = ".env" # Tạo file .env để lưu key

settings = Settings()