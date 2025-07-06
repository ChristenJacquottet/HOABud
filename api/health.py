from fastapi import FastAPI

app = FastAPI()

@app.get("/")    # Vercel mounts this at /api/health
async def health_check():
    return {"status": "ok"}