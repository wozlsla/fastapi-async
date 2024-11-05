from fastapi import Depends
from sqlalchemy import exists
from sqlalchemy.orm import Session

from shared.database.connection import get_db
from user.models import User


class UserRepository:
    """User 정보를 DB에 저장, 검색, 특정 username의 존재 여부 검증"""

    # get_db 라는 generator 의존성으로 주입
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # User 객체를 데이터베이스에 저장
    def save(self, user: User):
        self.db.add(user)  # 유저 객체 추가
        self.db.commit()  # 변경 사항을 커밋 -> 실제 데이터베이스에 반영

    # 유저 검색 (user_id)
    def get_user_by_id(self, user_id: int) -> User | None:
        # User 테이블에서 id 컬럼이 user_id와 일치하는 첫 번째 유저 객체를 반환 (없으면 None)
        return self.db.query(User).filter(User.id == user_id).first()

    # 유저 검색 (username)
    def get_user_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    # username이 DB에 존재하는지 확인
    def validate_username(self, username: str) -> bool:
        return not self.db.query(
            exists().where(User.username == username)
        ).scalar()  # Boolean
