from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from shared.authentication.jwt import InvalidTokenError, JWTPayloadTypedDict, JWTService


def _get_jwt(
    auth_header: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> str:
    if auth_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT Not provided",
        )
    return auth_header.credentials


# 헤더를 통해 JWT를 검증한 뒤 Token 안에 담긴 ID(사용자의 식별자) 반환
def authenticate(
    access_token: str = Depends(_get_jwt),
    jwt_service: JWTService = Depends(),
) -> int:
    try:
        payload: JWTPayloadTypedDict = jwt_service.decode_access_token(
            access_token=access_token
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    if not jwt_service.is_valid_token(payload=payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Expired",
        )
    return payload["user_id"]
