from fastapi import FastAPI

app = FastAPI()

@app.get("/visible")
def visible() -> dict[str, bool]:
    return {"scanned": True}
