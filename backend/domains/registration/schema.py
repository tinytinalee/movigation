# backend/domains/registration/schema.py

from typing import List

from pydantic import BaseModel, EmailStr, Field


# =========================
# REG-01-01 회원가입 요청
# =========================
class SignupRequest(BaseModel):
    """회원가입 요청 바디"""

    email: EmailStr
    password: str = Field(min_length=8)
    nickname: str = Field(min_length=1, max_length=30)


class SignupRequestResponse(BaseModel):
    """회원가입 요청 응답 (인증 메일 보낸 뒤)"""

    email: EmailStr
    expires_in: int  # seconds (예: 600)


# =========================
# REG-01-02 이메일 인증 확인
# =========================
class SignupConfirm(BaseModel):
    """이메일 인증 코드 확인 요청"""

    email: EmailStr
    code: str


class AuthToken(BaseModel):
    """JWT 토큰 응답 포맷"""

    access_token: str
    token_type: str = "bearer"


class SignupConfirmResponse(BaseModel):
    """회원가입 확정 + 자동 로그인 응답"""

    user_id: str
    email: EmailStr
    onboarding_completed: bool
    token: AuthToken


# =========================
# REG-03-01 OTT 선택
# =========================
class OnboardingOTTRequest(BaseModel):
    """온보딩: 구독 중인 OTT 플랫폼 선택"""

    provider_ids: List[int]


# =========================
# REG-04-01 취향 설문
# =========================
class OnboardingSurveyRequest(BaseModel):
    """온보딩: 영화 포스터 설문에서 선택한 영화들"""

    movie_ids: List[int]


# =========================
# REG-05-01 / 05-02 온보딩 완료 / 스킵
# =========================
class OnboardingCompleteResponse(BaseModel):
    """온보딩 완료/스킵 공통 응답"""

    user_id: str
    onboarding_completed: bool
