"""Short-link redirect endpoint for WhatsApp handoff URLs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.config import Settings, get_settings
from app.services.protocols import IShortLinkService

router = APIRouter(prefix="/api/r", tags=["short-links"])


def get_short_link_service(request: Request) -> IShortLinkService:
    return request.app.state.short_links


@router.get("/{code}")
async def resolve_short_link(code: str, request: Request) -> RedirectResponse:
    short_links = get_short_link_service(request)
    settings: Settings = get_settings()
    target_path = short_links.resolve(code)
    if target_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown or expired link",
        )
    return RedirectResponse(
        url=f"{settings.public_app_base_url.rstrip('/')}{target_path}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
