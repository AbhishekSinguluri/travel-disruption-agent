from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.trips import router as trips_router
from app.api.monitoring import router as mon_router
from app.api.voice import router as voice_router
from app.api.imports import router as imports_router

from app.services.booking_monitor import get_monitor_service

app = FastAPI(title="ROAM — Local Experience & Disruption AI Automator")

@app.on_event("startup")
async def startup_event():
    monitor_service = get_monitor_service()
    monitor_service.start()

@app.on_event("shutdown")
async def shutdown_event():
    monitor_service = get_monitor_service()
    monitor_service.stop()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

app.include_router(trips_router, prefix="/api/trips", tags=["trips"])
app.include_router(mon_router, prefix="/api/monitor", tags=["monitoring"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(imports_router, prefix="/api/import", tags=["import"])

from app.api.bookings import router as bookings_router
from app.api.gmail import router as gmail_router
from app.api.alerts import router as alerts_router
from app.api.monitor_test import router as monitor_test_router
from app.api.events import router as events_router
app.include_router(bookings_router, prefix="/api/bookings", tags=["bookings"])
app.include_router(gmail_router, prefix="/api/gmail", tags=["gmail"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
app.include_router(monitor_test_router, prefix="/api/monitor", tags=["monitor_test"])
app.include_router(events_router, prefix="/api/events", tags=["events"])



try:
    from app.api.bookings import router as bookings_router
    app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
except ImportError:
    pass


