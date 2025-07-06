import sys
import os
import tempfile
# Ensure project root is on Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
# Import Pydantic for data validation and settings management
from pydantic import BaseModel
# Import OpenAI client for interacting with OpenAI's API
from openai import OpenAI
import asyncio
from typing import Optional

# Imports for PDF processing and vector store
from aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel

# Initialize FastAPI application with a title
app = FastAPI(title="OpenAI Chat API", root_path="/api")

# Configure CORS (Cross-Origin Resource Sharing) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers in requests
)

# Global vector store for indexed PDFs
vector_db: VectorDatabase = None

# Define the data model for chat requests using Pydantic
class ChatRequest(BaseModel):
    developer_message: str  # Message from the developer/system
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4.1-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication

@app.post("/upload")
@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF, chunk it, create embeddings,
    and build a vector store for querying.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf allowed")
    tmp_dir = tempfile.gettempdir()
    save_dir = os.path.join(tmp_dir, "uploaded_files")
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, file.filename)
    # Save the uploaded PDF
    with open(path, "wb") as f:
        f.write(await file.read())
    # Load text from PDF
    docs = PDFLoader(path).load_documents()
    # Split into chunks
    chunks = CharacterTextSplitter().split_texts(docs)
    # Build embeddings and vector database
    db = await VectorDatabase(EmbeddingModel()).abuild_from_list(chunks)
    global vector_db
    vector_db = db
    return {"message": "Indexed", "num_chunks": len(chunks)}

@app.post("/chat")
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint that optionally uses the vector store
    to retrieve relevant PDF context.
    """
    try:
        # Initialize OpenAI client with the provided API key
        client = OpenAI(api_key=request.api_key)

        async def generate():
            # Assemble system (developer) message with PDF context if available
            if vector_db:
                # Retrieve top-k relevant chunks as text
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
            # Create a streaming chat completion request
            stream = client.chat.completions.create(
                model=request.model,
                messages=messages,
                stream=True,
            )
            # Yield each chunk of the response as it becomes available
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        # Handle any errors that occur during processing
        raise HTTPException(status_code=500, detail=str(e))

# Define a health check endpoint to verify API status
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
