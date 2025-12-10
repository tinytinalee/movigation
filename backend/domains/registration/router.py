from fastapi import APIRouter

router = APIRouter(tags=["registration"])


@router.post("/auth/signup/request")
def request_signup():
    return {"mock": "signup_request"}


@router.post("/auth/signup/confirm")
def confirm_signup():
    return {"mock": "signup_confirm"}


@router.post("/onboarding/ott")
def select_ott():
    return {"mock": "ott"}


@router.post("/onboarding/survey")
def survey():
    return {"mock": "survey"}


@router.post("/onboarding/complete")
def complete():
    return {"mock": "complete"}


@router.post("/onboarding/skip")
def skip():
    return {"mock": "skip"}
