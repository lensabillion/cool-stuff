from fastapi import FastAPI

app = FastAPI(title="CoolStuff - Minimal Check")

@app.get("/api/v1/health")

async def health():
    return {"ok": True}
