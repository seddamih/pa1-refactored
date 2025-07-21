import os
import shutil
import redis
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import threading

load_dotenv()

# Init Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "documents"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(index_name)
model = SentenceTransformer("all-MiniLM-L6-v2")
r = redis.Redis(host="redis", port=6379, decode_responses=True)

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === File Processing Logic ===
def extract_text_from_pdf(path):
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_image(path):
    return pytesseract.image_to_string(Image.open(path))

def get_text(path):
    ext = os.path.splitext(path)[-1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image(path)
    else:
        return ""

def handle_file_upload(path):
    text = get_text(path)
    if not text.strip():
        print(f"No text found in {path}")
        return
    embedding = model.encode(text)
    index.upsert(vectors=[{"id": path, "values": embedding.tolist()}])
    print(f"Indexed {path}")

# === Redis Listener in Thread ===
def redis_listener():
    pubsub = r.pubsub()
    pubsub.subscribe("file.upload")
    print("File agent is running...")
    for message in pubsub.listen():
        if message["type"] == "message":
            handle_file_upload(message["data"])

threading.Thread(target=redis_listener, daemon=True).start()

# === FastAPI App for Upload ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    r.publish("file.upload", file_path)
    return {"status": "ok", "filename": file.filename}

@app.get("/")
def read_root():
    return {"message": "Hello from file_agent!"}
