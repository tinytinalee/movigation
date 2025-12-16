# backend/models/movie.py

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.core.db import Base


class Movie(Base):
    """
    movies 테이블
    - 온보딩 설문 후보를 포함한 영화 메타데이터
    """

    __tablename__ = "movies"

    movie_id = Column(Integer, primary_key=True, autoincrement=True)
    tmdb_id = Column(Integer, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    genres = Column(String, nullable=True)
    runtime = Column(Integer, nullable=True)
    adult = Column(Boolean, nullable=False, server_default="false")
    popularity = Column(Float, nullable=True)
    tag_genome = Column(JSONB, nullable=True)

    onboarding_answers = relationship(
        "UserOnboardingAnswer",
        back_populates="movie",
        cascade="all, delete-orphan",
    )
    ott_mappings = relationship(
        "MovieOttMap",
        back_populates="movie",
        cascade="all, delete-orphan",
    )


class OttProvider(Base):
    """
    ott_providers 테이블
    - OTT 플랫폼(넷플릭스, 티빙 등) 목록
    """

    __tablename__ = "ott_providers"

    provider_id = Column(Integer, primary_key=True, autoincrement=True)
    provider_name = Column(String, nullable=False)
    logo_path = Column(String, nullable=True)

    user_mappings = relationship(
        "UserOttMap",
        back_populates="provider",
        cascade="all, delete-orphan",
    )
    movie_mappings = relationship(
        "MovieOttMap",
        back_populates="provider",
        cascade="all, delete-orphan",
    )


class MovieOttMap(Base):
    """
    movie_ott_map 테이블
    - 영화가 어떤 OTT에서 제공되는지 (N:N 매핑)
    """

    __tablename__ = "movie_ott_map"

    movie_id = Column(
        Integer,
        ForeignKey("movies.movie_id", ondelete="CASCADE"),
        primary_key=True,
    )
    provider_id = Column(
        Integer,
        ForeignKey("ott_providers.provider_id", ondelete="CASCADE"),
        primary_key=True,
    )
    link_url = Column(String, nullable=True)

    movie = relationship("Movie", back_populates="ott_mappings")
    provider = relationship("OttProvider", back_populates="movie_mappings")


class OnboardingCandidate(Base):
    """
    onboarding_candidates 테이블
    - 온보딩 설문용 영화 후보 (키워드별)
    """

    __tablename__ = "onboarding_candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(
        Integer,
        ForeignKey("movies.movie_id", ondelete="CASCADE"),
        nullable=False,
    )
    mood_tag = Column(String(50), nullable=False)
    display_order = Column(Integer, nullable=False)

    movie = relationship("Movie")
