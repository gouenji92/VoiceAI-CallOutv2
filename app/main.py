from fastapi import FastAPI
from app.routers import auth, workflows, calls

app = FastAPI(
    title="VoiceAI Backend API",
    description="API cho he thong AI Callbot (Da cap nhat Versioning & AI)",
    version="1.1.0"
)

# Gắn các router vào app chính
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
app.include_router(calls.router, prefix="/calls", tags=["Calls"])

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Welcome to VoiceAI API"}