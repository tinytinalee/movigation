# backend/domains/registration/service.py

from sqlalchemy.orm import Session

from backend.services.mail_service import (
    generate_signup_code,
    send_signup_code_email,
)

from .schema import (
    OnboardingCompleteResponse,
    OnboardingOTTRequest,
    OnboardingSurveyRequest,
    SignupConfirm,
    SignupConfirmResponse,
    SignupRequest,
    SignupRequestResponse,
)

SIGNUP_CODE_TTL = 600  # 프론트에 알려줄 만료 시간(초 단위, 지금은 그냥 상수)


# -----------------------------
# REG-01-01 회원가입 요청
# -----------------------------
def request_signup(db: Session, payload: SignupRequest) -> SignupRequestResponse:
    """
    1) 인증번호 생성
    2) 메일 발송
    3) 프론트에 email + expires_in 리턴

    지금 단계에선 DB/Redis에 코드 저장은 안 함.
    (프론트/백 둘 다 흐름 맞추는 용도)
    """

    code = generate_signup_code()

    # TODO: 나중에 여기서 code를 Redis나 임시 테이블에 저장하면 됨.
    send_signup_code_email(payload.email, code)

    return SignupRequestResponse(
        email=payload.email,
        expires_in=SIGNUP_CODE_TTL,
    )


# -----------------------------
# REG-01-02 회원가입 확인
# (지금은 아직 미구현)
# -----------------------------
def confirm_signup(db: Session, payload: SignupConfirm) -> SignupConfirmResponse:
    raise NotImplementedError("회원가입 확인 로직은 아직 미구현입니다.")


# -----------------------------
# 나머지 온보딩 관련 함수는
# 일단 형태만 잡아두고 나중에 구현
# -----------------------------
def save_user_ott(db: Session, user, payload: OnboardingOTTRequest) -> None:
    raise NotImplementedError


def save_onboarding_answers(
    db: Session, user, payload: OnboardingSurveyRequest
) -> None:
    raise NotImplementedError


def complete_onboarding(db: Session, user) -> OnboardingCompleteResponse:
    raise NotImplementedError


def skip_onboarding(db: Session, user) -> OnboardingCompleteResponse:
    raise NotImplementedError
