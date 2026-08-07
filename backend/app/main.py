"""
MEMFORENSIX FastAPI application entry point.
"""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analysis, auth, results, upload, websocket
from app.core.config import settings

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger("memforensix")

app = FastAPI(
    title=settings.APP_NAME,
    description="Digital Forensics Tool for Memory Dump Analysis",
    version="1.0.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info("%s %s -> %s (%.1fms)", request.method, request.url.path,
                response.status_code, duration_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(upload.router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis.router, prefix=settings.API_V1_PREFIX)
app.include_router(results.router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/", tags=["health"])
async def root():
    return {"message": f"{settings.APP_NAME} API", "docs": f"{settings.API_V1_PREFIX}/docs"}
