# backend/domains/registration/router.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.core.db import get_db
from backend.models.user import User

from . import service
from .schema import (
    OnboardingCompleteResponse,
    OnboardingOTTRequest,
    OnboardingSurveyRequest,
    SignupConfirm,
    SignupConfirmResponse,
    SignupRequest,
    SignupRequestResponse,
)

router = APIRouter(tags=["registration"])


# =========================
# REG-01-01 회원가입 요청
# =========================
@router.post(
    "/auth/signup/request",
    response_model=SignupRequestResponse,
    summary="회원가입 요청 (인증 메일 발송)",
)
def request_signup(
    payload: SignupRequest,
    db: Session = Depends(get_db),
) -> SignupRequestResponse:
    """
    회원가입 이메일 + 비밀번호 + 닉네임을 받고,
    - 이미 가입된 이메일인지 검사
    - Redis에 인증정보 + 코드 저장
    - 인증코드 메일 발송

    성공 시, 인증 만료 시간(expires_in)을 함께 반환한다.
    """
    return service.request_signup(db, payload)


# =========================
# REG-01-02 이메일 인증 확인
# =========================
@router.post(
    "/auth/signup/confirm",
    response_model=SignupConfirmResponse,
    summary="이메일 인증 코드 확인 및 회원가입 확정",
)
def confirm_signup(
    payload: SignupConfirm,
    db: Session = Depends(get_db),
) -> SignupConfirmResponse:
    """
    이메일과 인증 코드를 받아 Redis에 저장된 값과 비교하고,
    - 코드가 유효하면 실제 User를 생성
    - JWT 액세스 토큰을 발급하여 반환한다.
    """
    return service.confirm_signup(db, payload)


# =========================
# REG-03-01 온보딩 – OTT 선택
# =========================
@router.post(
    "/onboarding/ott",
    summary="온보딩: 구독 중인 OTT 플랫폼 선택",
)
def select_ott(
    payload: OnboardingOTTRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    유저가 구독 중인 OTT(provider_id 리스트)를 저장한다.
    기존 값은 모두 삭제 후 새로 저장하는 idempotent 동작이다.
    """
    service.save_user_ott(db, current_user, payload)
    return {"status": "ok"}


# =========================
# REG-04-01 온보딩 – 취향 설문
# =========================
@router.post(
    "/onboarding/survey",
    summary="온보딩: 영화 포스터 설문 응답 저장",
)
def survey(
    payload: OnboardingSurveyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    온보딩 영화 설문에서 유저가 선택한 movie_id 리스트를 저장한다.
    기존 응답은 삭제 후 새로 저장한다.
    """
    service.save_onboarding_answers(db, current_user, payload)
    return {"status": "ok"}


# =========================
# REG-05-01 온보딩 완료
# =========================
@router.post(
    "/onboarding/complete",
    response_model=OnboardingCompleteResponse,
    summary="온보딩 완료 처리",
)
def complete(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OnboardingCompleteResponse:
    """
    온보딩을 완료 상태로 변경한다.
    추후 벡터 생성 등 후처리 작업은 이 시점에 트리거할 수 있다.
    """
    return service.complete_onboarding(db, current_user)


# =========================
# REG-05-02 온보딩 스킵
# =========================
@router.post(
    "/onboarding/skip",
    response_model=OnboardingCompleteResponse,
    summary="온보딩 스킵 처리",
)
def skip(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OnboardingCompleteResponse:
    """
    온보딩을 스킵한다.
    스펙 상 onboarding_completed 플래그는 변경하지 않고,
    현재 상태를 그대로 응답으로 반환한다.
    """
    return service.skip_onboarding(db, current_user)
