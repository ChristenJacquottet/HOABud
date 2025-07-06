import sys, os, tempfile
from fastapi import FastAPI, HTTPException, File, UploadFile
from aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel

app = FastAPI()
vector_db: VectorDatabase = None

@app.post("/")   # Vercel will mount this at /api/upload
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