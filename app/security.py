import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


security = HTTPBearer()


API_KEYS = {
    os.getenv("GATEWAY_DEV_KEY", "gateway-dev-key"): {
        "client_id": "dev-client",
        "role": "user",
    },
    os.getenv("GATEWAY_ADMIN_KEY", "gateway-admin-key"): {
        "client_id": "admin-client",
        "role": "admin",
    },
}


def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:

    token = credentials.credentials

    client = API_KEYS.get(token)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return client