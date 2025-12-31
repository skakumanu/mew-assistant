from fastapi import APIRouter

router = APIRouter()


@router.post("/confirm")
async def confirm_session():
    """Confirm session endpoint."""
