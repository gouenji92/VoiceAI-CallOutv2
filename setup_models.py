"""
Script tự động tải và setup PhoBERT models
Chạy sau khi clone repository lần đầu
"""
import os
from pathlib import Path

def setup_phobert_model():
    """Download và setup PhoBERT intent classifier"""
    print("="*60)
    print("  SETUP PHOBERT INTENT CLASSIFIER")
    print("="*60)
    
    model_dir = Path("./models/phobert-intent-classifier")
    
    # Kiểm tra xem model đã tồn tại chưa
    if model_dir.exists() and (model_dir / "config.json").exists():
        print("✅ Model đã tồn tại, không cần download")
        return True
    
    print("\n📦 Model chưa có, đang train từ đầu...")
    print("   (Sẽ mất ~5-10 phút)")
    
    # Tạo thư mục nếu chưa có
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Chạy train script
    print("\n🔥 Bắt đầu train model...")
    import subprocess
    result = subprocess.run(
        ["python", "train_intent_model.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Train model thành công!")
        print(f"   Model đã lưu tại: {model_dir.absolute()}")
        return True
    else:
        print("❌ Lỗi khi train model:")
        print(result.stderr)
        return False

def verify_installation():
    """Kiểm tra tất cả dependencies"""
    print("\n" + "="*60)
    print("  KIỂM TRA CÀI ĐẶT")
    print("="*60)
    
    checks = []
    
    # 1. Python packages
    print("\n1️⃣ Kiểm tra Python packages...")
    required_packages = [
        "fastapi",
        "uvicorn",
        "supabase",
        "transformers",
        "torch",
        "bcrypt",
        "python-jose"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {package}")
            checks.append(True)
        except ImportError:
            print(f"   ❌ {package} - chưa cài")
            checks.append(False)
    
    # 2. Model files
    print("\n2️⃣ Kiểm tra model files...")
    model_files = [
        "./models/phobert-intent-classifier/config.json",
        "./models/phobert-intent-classifier/model.safetensors",
        "./models/phobert-intent-classifier/tokenizer_config.json"
    ]
    
    for file_path in model_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
            checks.append(True)
        else:
            print(f"   ❌ {file_path} - chưa có")
            checks.append(False)
    
    # 3. Environment file
    print("\n3️⃣ Kiểm tra environment file...")
    if Path(".env").exists():
        print("   ✅ .env file tồn tại")
        checks.append(True)
    else:
        print("   ⚠️  .env file chưa có")
        print("      Copy từ .env.example và điền thông tin Supabase")
        checks.append(False)
    
    # Kết quả
    print("\n" + "="*60)
    success_rate = sum(checks) / len(checks) * 100
    print(f"  Tỷ lệ hoàn thành: {success_rate:.0f}%")
    print("="*60)
    
    return all(checks)

def main():
    print("\n🚀 VOICEAI - AUTO SETUP SCRIPT")
    print("="*60)
    
    # 1. Verify dependencies
    print("\n📋 Bước 1: Kiểm tra dependencies...")
    
    # 2. Setup models
    print("\n📋 Bước 2: Setup PhoBERT models...")
    model_ok = setup_phobert_model()
    
    # 3. Final verification
    all_ok = verify_installation()
    
    # Summary
    print("\n" + "="*60)
    print("  KẾT QUẢ SETUP")
    print("="*60)
    
    if all_ok:
        print("\n🎉 HOÀN TẤT! Hệ thống sẵn sàng!")
        print("\n📝 BƯỚC TIẾP THEO:")
        print("   1. Copy .env.example thành .env")
        print("   2. Điền SUPABASE_URL và SUPABASE_KEY vào .env")
        print("   3. Chạy: python -X utf8 -m uvicorn app.main:app --reload")
        print("   4. Test: python test_full_system.py")
    else:
        print("\n⚠️  CÒN MỘT SỐ VẤN ĐỀ CẦN FIX")
        print("   Xem chi tiết bên trên và fix các mục ❌")
        
        if not Path(".env").exists():
            print("\n💡 TẠO .ENV FILE:")
            print("   cp .env.example .env")
            print("   # Sau đó edit .env và điền thông tin Supabase")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup bị dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
