import sys, os, tempfile
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI

from aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel

app = FastAPI(title="HOA Bud API")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_db: VectorDatabase = None

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only .pdf allowed")
    save_dir = os.path.join(tempfile.gettempdir(), "uploaded_files")
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, file.filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    docs = PDFLoader(path).load_documents()
    chunks = CharacterTextSplitter().split_texts(docs)
    global vector_db
    vector_db = await VectorDatabase(EmbeddingModel()).abuild_from_list(chunks)
    return {"message": "Indexed", "num_chunks": len(chunks)}

class ChatRequest(BaseModel):
    developer_message: str
    user_message:     str
    model: Optional[str] = "gpt-4.1-mini"
    api_key: str

@app.post("/chat")
async def chat(request: ChatRequest):
    client = OpenAI(api_key=request.api_key)

    async def generate():
        global vector_db
        if vector_db:
            context_chunks = vector_db.search_by_text(
                request.user_message, k=5, return_as_text=True
            )
            context = "\n\n".join(context_chunks)
            sys_content = f"{request.developer_message}\n\nUse these docs:\n{context}"
        else:
            sys_content = request.developer_message

        messages = [
            {"role": "system", "content": sys_content},
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

@app.get("/health")
async def health():
    return {"status": "ok"}

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)