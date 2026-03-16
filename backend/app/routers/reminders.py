from fastapi import APIRouter

from app.models.schemas import ReminderRequest

router = APIRouter()


@router.post("/")
async def setup_reminders(request: ReminderRequest):
    """Set up SMS reminders for parsed events."""
    # TODO: call sms service
    return {"status": "not implemented"}
