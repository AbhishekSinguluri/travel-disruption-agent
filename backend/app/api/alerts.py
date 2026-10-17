
from fastapi import APIRouter
from app.db.repositories import get_booking_repository

router = APIRouter()

@router.get("/")
async def get_alerts(user_id: str = "demo-user"):
    repo = get_booking_repository()
    return repo.get_alerts(user_id)
