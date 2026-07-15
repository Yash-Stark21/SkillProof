from fastapi import FastAPI

app = FastAPI()

@app.get("/api/profile")
def profile() -> dict[str, str]:
    return {"name": "Ada"}
