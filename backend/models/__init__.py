# backend/models/__init__.py

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """모든 ORM 모델이 상속할 공통 Base 클래스"""

    pass
