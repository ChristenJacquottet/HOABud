from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import api.upload as upload_module

app = FastAPI()

class ChatRequest(BaseModel):
    developer_message: str
    user_message:     str
    model: Optional[str] = "gpt-4.1-mini"
    api_key: str

@app.post("/")   # Vercel mounts this at /api/chat
async def chat(request: ChatRequest):
    client = OpenAI(api_key=request.api_key)

    async def generate():
        vector_db = upload_module.vector_db
        if vector_db:
            context_chunks = vector_db.search_by_text(
                request.user_message, k=5, return_as_text=True
            )
            context = "\n\n".join(context_chunks)
            sys_content = f"{request.developer_message}\n\nUse these docs:\n{context}"
        else:
            sys_content = request.developer_message

        messages = [
            {"role": "developer", "content": sys_content},
            {"role": "user", "content": request.user_message},
        ]
        stream = client.chat.completions.create(
            model=request.model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    try:
        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))