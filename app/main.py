from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.routers import auth, workflows, calls, feedback, admin, rl_monitor
from app.dependencies import get_settings

settings = get_settings()

app = FastAPI(
    title="VoiceAI Backend API",
    description="API cho he thong AI Callbot (Da cap nhat Versioning & AI)",
    version="1.1.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins (development only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thêm Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Gắn các router vào app chính
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(calls.router, prefix="/api/calls", tags=["Calls"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(rl_monitor.router, prefix="/api/rl-monitor", tags=["RL Monitoring"])

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Welcome to VoiceAI API"}