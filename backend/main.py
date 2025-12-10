from fastapi import FastAPI

app = FastAPI()

from backend.domains.registration.router import router as registration_router

app.include_router(registration_router)


@app.get("/")
def root():
    return {"message": "ok"}
