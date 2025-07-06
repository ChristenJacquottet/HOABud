import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from api.upload import app as upload_app
from api.chat   import app as chat_app
from api.health import app as health_app

app = FastAPI(title="HOA Bud API", root_path="/api")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount the three sub‐apps
app.mount("/upload", upload_app)
app.mount("/chat",   chat_app)
app.mount("/health", health_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
