from fastapi import Depends, FastAPI

app = FastAPI()

def current_user() -> str:
    return "fixture-user"

@app.get("/health")
def health(user: str = Depends(current_user)) -> dict[str, str]:
    return {"status": "ok", "user": user}
