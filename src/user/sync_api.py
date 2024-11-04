from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from shared.authentication.dependency import authenticate
from shared.authentication.jwt import JWTService
from shared.authentication.password import PasswordService
from user.models import User
from user.request import UserAuthRequest
from user.response import UserResponse, UserTokenResponse
from user.sync_repository import UserRepository


# 1. 라우터 정의
# APIRouter 객체를 생성, /users로 시작하는 경로를 관리
# tags : API 문서에서 이 경로들을 "Users"라는 그룹으로 묶음
router = APIRouter(prefix="/users", tags=["Users"])


# 2. 회원가입 핸들러
# /users/sign-up 경로에 POST 요청을 보내 호출
@router.post(
    "/sign-up",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
def user_sign_up_handler(
    # 데이터 모델(UserAuthRequest)로부터 요청 바디를 받아옴 - username, pw
    body: UserAuthRequest,
    # UserRepository 객체를 받아 사용자 DB 연산에 사용
    user_repo: UserRepository = Depends(),
    # PasswordService 객체를 받아 비밀번호 해싱 작업에 사용
    password_service: PasswordService = Depends(),
):
    # 사용자명 중복 확인
    if not user_repo.validate_username(username=body.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    # 사용자 생성
    new_user = User.create(
        username=body.username,
        password_hash=password_service.hash_password(
            plain_text=body.password
        ),  # pw 해시 처리
    )
    user_repo.save(user=new_user)

    # 성공적으로 저장되면 새 사용자 정보를 UserResponse 형태로 반환
    return UserResponse.build(user=new_user)


# 3. 로그인 핸들러
@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserTokenResponse,
)
def user_login_handler(
    body: UserAuthRequest,
    user_repo: UserRepository = Depends(),
    # JWTService 객체를 받아 JWT 토큰 생성
    jwt_service: JWTService = Depends(),
    password_service: PasswordService = Depends(),
):
    # username을 통해 사용자 조회
    user: User | None = user_repo.get_user_by_username(username=body.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 비밀번호 검증 (사용자가 입력한 PW == DB에 저장된 해시값 비교)
    if not password_service.check_password(
        plain_text=body.password, hashed_password=user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    # 성공 시 JWT access 토큰을 생성하여 반환
    access_token = jwt_service.encode_access_token(user_id=user.id)
    return UserTokenResponse.build(access_token=access_token)


# 4. 내 정보 조회 핸들러
# /users/me 경로에 GET 요청을 보내 호출
@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
def get_me_handler(
    # authenticate 함수를 통해 사용자 인증을 수행(login API에서 발급한 JWT를 넘겨줘야 함)하고, 사용자 ID를 반환받음
    me_id: int = Depends(authenticate),
    user_repo: UserRepository = Depends(),
):
    # Token 인증을 통과한 사용자 ID를 통해 DB에서 사용자 조회, 반환
    user: User | None = user_repo.get_user_by_id(user_id=me_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 성공 시 사용자 정보를 반환
    return UserResponse.build(user=user)
