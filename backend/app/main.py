"""
FastAPI application entry point.

Environment variables:
  CORS_ORIGINS   — comma-separated list of allowed origins
                   e.g. "https://election-forecast-489820.web.app,http://localhost:5173"
  ADMIN_SECRET   — secret token for the /api/forecast/refresh endpoint
  PORT           — TCP port (default 8080, used by Cloud Run)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.forecast import router as forecast_router

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Election Forecast API",
    description="2028 US Senate forecast — Monte Carlo simulation",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ───────────────────────────────────────────────────────────────────────

_raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173",
)
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────

app.include_router(forecast_router, prefix="/api")


@app.get("/healthz", include_in_schema=False)
async def health():
    return {"status": "ok"}
