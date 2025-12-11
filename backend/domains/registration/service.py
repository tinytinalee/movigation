# backend/domains/registration/service.py

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.core.auth import create_access_token  # JWT 발급 함수
from backend.models.user import User, UserOnboardingAnswer, UserOttMap
from backend.services.mail_service import (
    generate_signup_code,
    send_signup_code_email,
)
from backend.utils.password import hash_password
from backend.utils.redis import get_redis_client

from .schema import (
    OnboardingCompleteResponse,
    OnboardingOTTRequest,
    OnboardingSurveyRequest,
    SignupConfirm,
    SignupConfirmResponse,
    SignupRequest,
    SignupRequestResponse,
)

# ========================================
# 설정 값
# ========================================
SIGNUP_CODE_TTL = 600  # 10분 (초 단위)
SIGNUP_REDIS_KEY = "signup:{email}"


def _redis_key(email: str) -> str:
    """Redis Key 생성"""
    return SIGNUP_REDIS_KEY.format(email=email)


# ========================================
# REG-01-01 회원가입 요청
# ========================================
def request_signup(db: Session, payload: SignupRequest) -> SignupRequestResponse:
    """
    회원가입 요청 처리:
    - 이미 가입된 이메일인지 체크
    - 임시 인증 코드 생성
    - Redis에 이메일/비밀번호/닉네임/코드 저장
    - 인증 코드 메일 발송
    """
    # 이미 가입된 이메일인지 체크
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 이메일입니다.",
        )

    # 인증 코드 생성 (6자리 숫자)
    code = generate_signup_code()

    # Redis 저장
    redis = get_redis_client()
    key = _redis_key(payload.email)

    redis.hset(
        key,
        mapping={  # type: ignore[arg-type]
            "email": payload.email,
            "password": hash_password(payload.password),
            "nickname": payload.nickname,
            "code": code,
        },
    )
    redis.expire(key, SIGNUP_CODE_TTL)

    # 메일 발송 (SMTP 환경변수 없으면 콘솔에만 출력)
    send_signup_code_email(payload.email, code)

    return SignupRequestResponse(email=payload.email, expires_in=SIGNUP_CODE_TTL)


# ========================================
# REG-01-02 이메일 인증 후 실제 유저 생성
# ========================================
def confirm_signup(db: Session, payload: SignupConfirm) -> SignupConfirmResponse:
    """
    이메일 + 인증 코드 확인:
    - Redis에서 임시 데이터 조회
    - 코드 검증
    - 실제 User 생성
    - Redis 데이터 삭제
    - JWT 액세스 토큰 발급
    """
    redis = get_redis_client()
    key = _redis_key(payload.email)

    data = redis.hgetall(key)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 정보가 만료되었거나 존재하지 않습니다.",
        )

    stored_code = data.get(b"code", b"").decode()
    if stored_code != payload.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 코드가 올바르지 않습니다.",
        )

    # 중복 가입 방지 (이 타이밍에도 다시 체크)
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 이메일입니다.",
        )

    # 실제 유저 생성
    user = User(
        email=data[b"email"].decode(),
        password=data[b"password"].decode(),
        onboarding_completed=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Redis 데이터 삭제
    redis.delete(key)

    # JWT 발급
    token = create_access_token({"sub": str(user.user_id)})

    return SignupConfirmResponse(
        user_id=str(user.user_id),
        email=user.email,
        onboarding_completed=user.onboarding_completed,
        token={
            "access_token": token,
            "token_type": "bearer",
        },
    )


# ========================================
# REG-03-01 온보딩 – OTT 선택
# ========================================
def save_user_ott(db: Session, user: User, payload: OnboardingOTTRequest) -> None:
    """
    유저가 구독 중인 OTT(provider_id 리스트)를 저장.
    기존 기록은 모두 삭제 후 다시 저장한다 (idempotent).
    """
    # 기존 데이터 삭제 후 다시 저장 (idempotent)
    db.execute(delete(UserOttMap).where(UserOttMap.user_id == user.user_id))

    for provider_id in payload.provider_ids:
        db.add(UserOttMap(user_id=user.user_id, provider_id=provider_id))

    db.commit()


# ========================================
# REG-04-01 온보딩 – 영화 포스터 설문
# ========================================
def save_onboarding_answers(
    db: Session,
    user: User,
    payload: OnboardingSurveyRequest,
) -> None:
    """
    온보딩 영화 설문에서 유저가 선택한 movie_id 목록을 저장.
    기존 응답은 삭제 후 새로 저장한다.
    """
    now = datetime.utcnow()

    # 기존 기록 삭제 후 새로 저장
    db.execute(
        delete(UserOnboardingAnswer).where(UserOnboardingAnswer.user_id == user.user_id)
    )

    for movie_id in payload.movie_ids:
        db.add(
            UserOnboardingAnswer(
                user_id=user.user_id,
                movie_id=movie_id,
                selected_at=now,
            )
        )

    db.commit()


# ========================================
# REG-05-01 온보딩 완료
# ========================================
def complete_onboarding(db: Session, user: User) -> OnboardingCompleteResponse:
    """
    온보딩 완료 처리.
    플래그를 True로 바꾸고, 후처리(벡터 생성 등)는 추후 추가 가능.
    """
    user.onboarding_completed = True
    db.add(user)
    db.commit()
    db.refresh(user)

    # ⚠️ TODO: Celery로 "유저 벡터 생성" 트리거하기
    # from backend.services.ai_gateway import trigger_vector_update
    # trigger_vector_update.delay(str(user.user_id))

    return OnboardingCompleteResponse(
        user_id=str(user.user_id),
        onboarding_completed=True,
    )


# ========================================
# REG-05-02 온보딩 스킵
# ========================================
def skip_onboarding(db: Session, user: User) -> OnboardingCompleteResponse:
    """
    온보딩 스킵 처리.
    onboarding_completed 값은 변경하지 않고 현재 상태를 그대로 반환한다.
    """
    # 스펙 상 onboarding_completed=False 유지
    return OnboardingCompleteResponse(
        user_id=str(user.user_id),
        onboarding_completed=user.onboarding_completed,
    )
