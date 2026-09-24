from fastapi import Depends, HTTPException, status

from app.security import authenticate


def require_user(
    client: dict = Depends(authenticate),
) -> dict:
    """
    Authorization dependency.

    Allows both normal users and admins to access
    user-level endpoints.
    """

    if client["role"] not in {"user", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return client


def require_admin(
    client: dict = Depends(authenticate),
) -> dict:
    """
    Authorization dependency for admin-only endpoints.
    """

    if client["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return client