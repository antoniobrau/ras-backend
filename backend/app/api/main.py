from fastapi import FastAPI
from app.api.v1.health import router as health_router
from app.api.v1.me import router as me_router

app = FastAPI(title="RAS Assistant API")

app.include_router(health_router)
app.include_router(me_router)