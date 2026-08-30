import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

router = APIRouter()


@router.get("/")
async def landing_page(request: Request):
    """
    A browser landing on the bare domain goes straight to sign-in.

    This used to render its own hardcoded HTML with "Sign in with
    Google/Microsoft" buttons pointing at /auth/simple/* - routes that no
    longer exist since WorkOS AuthKit (app/routers/oauth_workos.py) became
    the single sign-in front door. Redirecting here instead of maintaining
    a second, easily-forgotten copy of the sign-in page means there is only
    one entry point to keep working.
    """
    # During tests or when an API client requests JSON, return a small JSON payload
    if os.getenv("TESTING") == "true" or "application/json" in request.headers.get("accept", ""):
        return JSONResponse(
            {
                "status": "ok",
                "service": "Mew Assistant",
                "message": "Mew Assistant is running",
            }
        )

    return RedirectResponse(url="/app/sign-in")
