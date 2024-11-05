from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.config import settings


# Sync
def get_engine():
    db_engine = create_engine(settings.db_url, pool_pre_ping=True)
    return db_engine


engine = get_engine()
SessionFactory = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)


# SQLAlchemy의 세션 객체 반환
def get_db() -> Generator[Session, None, None]:
    db = SessionFactory()  # 데이터베이스 세션을 생성
    try:
        yield db  # generator 생성
    finally:
        db.close()  # generator가 종료될 때 항상 실행
