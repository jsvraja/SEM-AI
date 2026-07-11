from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import ALLOWED_ORIGINS
from app.routers import reports, auth, billing
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SEM AI Platform", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(billing.router)


@app.get("/")
async def root():
    return {"status": "SEM AI Platform running", "version": "2.0.0"}
