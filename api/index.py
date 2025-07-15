import sys, os, tempfile, pickle
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

# Define a path in the Vercel-writable /tmp directory
VECTOR_DB_PATH = os.path.join(tempfile.gettempdir(), "vector_db.pkl")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only .pdf allowed")

    # Save the uploaded file temporarily
    temp_dir = os.path.join(tempfile.gettempdir(), "uploaded_files")
    os.makedirs(temp_dir, exist_ok=True)
    path = os.path.join(temp_dir, file.filename)
    
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    # Process the PDF and build the vector database
    docs = PDFLoader(path).load_documents()
    chunks = CharacterTextSplitter().split_texts(docs)
    vector_db = await VectorDatabase(EmbeddingModel()).abuild_from_list(chunks)

    vector_db.embedding_model = None
    
    # Save the processed vector_db to a file for persistence
    with open(VECTOR_DB_PATH, "wb") as f:
        pickle.dump(vector_db, f)

    # Clean up the temporary PDF file
    os.remove(path)
    
    return {"message": "Indexed", "num_chunks": len(chunks)}

class ChatRequest(BaseModel):
    developer_message: str
    user_message: str
    model: Optional[str] = "gpt-4o-mini"
    api_key: str

@app.post("/chat")
async def chat(request: ChatRequest):
    client = OpenAI(api_key=request.api_key)

    async def generate():
        vector_db_instance = None
        # Load the vector database from the file if it exists
        if os.path.exists(VECTOR_DB_PATH):
            with open(VECTOR_DB_PATH, "rb") as f:
                vector_db_instance = pickle.load(f)

            vector_db_instance.embedding_model = EmbeddingModel()

        if vector_db_instance:
            context_chunks = vector_db_instance.search_by_text(
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
    uvicorn.run(app, host="0.0.0.0", port=8000)