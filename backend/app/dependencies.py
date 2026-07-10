from __future__ import annotations

from collections.abc import Generator

from fastapi import Header, HTTPException, Request, status
from sqlalchemy.orm import Session


def get_session(request: Request) -> Generator[Session, None, None]:
    yield from request.app.state.database.session()


def require_read(request: Request) -> None:
    settings = request.app.state.settings
    if not settings.public_reads:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public reads are disabled.",
        )


def require_write(
    request: Request,
    x_sc_api_key: str | None = Header(default=None, alias="X-SC-API-Key"),
) -> None:
    settings = request.app.state.settings
    expected = settings.write_api_key

    if not expected:
        if settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Writes are disabled because no production write key is configured.",
            )
        return

    if x_sc_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-SC-API-Key header is required.",
        )
