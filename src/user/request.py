from pydantic import BaseModel, Field


# User 데이터 모델
class UserAuthRequest(BaseModel):
    username: str = Field(..., examples=["admin"])
    password: str = Field(..., examples=["1234"])
