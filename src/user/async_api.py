from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from shared.authentication.dependency import authenticate
from shared.authentication.jwt import JWTService
from shared.authentication.password import PasswordService
from user.models import User
from user.request import UserAuthRequest
from user.response import UserResponse, UserTokenResponse
from user.async_repository import UserRepository


router = APIRouter(prefix="/users", tags=["Users"])


# Sign-up 핸들러
@router.post(
    "/sign-up",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def user_sign_up_handler(
    body: UserAuthRequest,
    user_repo: UserRepository = Depends(),
    password_service: PasswordService = Depends(),
):
    # 비동기) username 중복 검사
    if not await user_repo.validate_username(username=body.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    # 동기) 사용자 생성
    new_user = User.create(
        username=body.username,  # user 인스턴스 생성
        password_hash=password_service.hash_password(
            plain_text=body.password
        ),  # hashing
    )
    await user_repo.save(user=new_user)  # 비동기) DB에 저장(I/O 대기 발생)
    return UserResponse.build(user=new_user)


# Login Handler
@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserTokenResponse,
)
async def user_login_handler(
    body: UserAuthRequest,
    user_repo: UserRepository = Depends(),
    jwt_service: JWTService = Depends(),
    password_service: PasswordService = Depends(),
):
    # 비동기) repository에서 사용자 조회
    user: User | None = await user_repo.get_user_by_username(username=body.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 동기) 비밀번호 검증 (사용자가 입력한 PW == DB에 저장된 해시값 비교)
    if not password_service.check_password(
        plain_text=body.password, hashed_password=user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    # 동기) 성공 시 access 토큰을 생성(JWT encoding)하여 반환
    access_token = jwt_service.encode_access_token(user_id=user.id)
    return UserTokenResponse.build(access_token=access_token)


# My-page Handler
@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
async def get_me_handler(
    me_id: int = Depends(authenticate),
    user_repo: UserRepository = Depends(),
):
    # 사용자 ID DB 조회
    user: User | None = await user_repo.get_user_by_id(user_id=me_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.build(user=user)
