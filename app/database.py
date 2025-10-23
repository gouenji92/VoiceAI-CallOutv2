from supabase import create_client, Client
from app.config import settings

try:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    print("Ket noi Supabase thanh cong!") # Đã sửa lỗi Unicode
except Exception as e:
    print(f"Loi khi khoi tao Supabase: {e}")