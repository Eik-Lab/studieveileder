import os
import uuid
from pathlib import Path
from typing import List
import numpy as np
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 1200
OVERLAP = 200


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - OVERLAP
        if start < 0:
            start = 0
    return [c.strip() for c in chunks if c.strip()]


def get_embeddings(texts: List[str]) -> List[List[float]]:
    r = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [d.embedding for d in r.data]


def store_embeddings(chunks: List[str], embeddings: List[List[float]], source: str):
    rows = []
    for text, emb in zip(chunks, embeddings):
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "content": text,
                "embedding": emb,
                "source": source,
            }
        )
    supabase.table("embeddings").insert(rows).execute()


def process_folder(folder: str):
    for path in Path(folder).rglob("*"):
        if path.is_file():
            text = read_file(path)
            chunks = chunk_text(text)
            if not chunks:
                continue
            embeddings = get_embeddings(chunks)
            store_embeddings(chunks, embeddings, str(path))


if __name__ == "__main__":
    process_folder("parsing-python/subject_contents")
