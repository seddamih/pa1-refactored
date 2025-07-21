import os
import redis, fitz, pytesseract, openai
from PIL import Image
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Pinecone + model init
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("documents")
model = SentenceTransformer("all-MiniLM-L6-v2")
r = redis.Redis(host="redis", port=6379, decode_responses=True)

UPLOAD_DIR = "/app/uploads"

def extract_text(path):
    ext = os.path.splitext(path)[-1].lower()
    if ext == ".pdf":
        text = ""
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif ext in [".png", ".jpg", ".jpeg"]:
        return pytesseract.image_to_string(Image.open(path))
    return ""

def summarize(text):
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role":"system","content":"Summarize the document concisely."},
                  {"role":"user","content":text[:2000]}]
    )
    return resp.choices[0].message.content

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.post("/search")
async def search(req: dict):
    q_emb = model.encode(req["query"]).tolist()
    res = index.query(vector=q_emb, top_k=5, include_values=False)
    if not res.matches:
        return {"results": []}
    results = []
    for m in res.matches:
        file_id = m.id
        score = m.score
        path = file_id  # expecting full path
        text = extract_text(path)
        summary = summarize(text)
        results.append({"id": file_id, "score": score, "summary": summary})
    return {"results": results}

@app.get("/")
def read_root():
    return {"message": "Hello from search_agent!"}
