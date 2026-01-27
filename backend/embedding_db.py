import os
import json
import re
from typing import List

import psycopg
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATABASE_URL = os.getenv("DATABASE_URL")

EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4.1-mini"

CHUNK_SIZE = 600


def split_paragraphs(text: str) -> List[str]:

    return [
        p.strip()
        for p in re.split(r"\n\s*\n+", text)
        if p.strip()
    ]


def chunk_text(text: str, max_size: int = CHUNK_SIZE) -> List[str]:

    paragraphs = split_paragraphs(text)

    chunks = []
    buffer = ""

    for para in paragraphs:

        if len(buffer) + len(para) <= max_size:

            buffer += ("\n\n" if buffer else "") + para

        else:

            chunks.append(buffer.strip())
            buffer = para

    if buffer:
        chunks.append(buffer.strip())

    return chunks


def add_context_to_chunk(document: str, chunk: str) -> str:

    prompt = f"""
Summarize this chunk in relation to the document in ONE sentence (max 20 words).

Document:
{document[:500]}

Chunk:
{chunk[:800]}
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You write retrieval context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    context = response.choices[0].message.content.strip()

    return f"{context}\n\n{chunk}"


def get_embeddings(texts: List[str], max_chars: int = 6000) -> List[List[float]]:

    safe_texts = []

    for t in texts:

        if len(t) > max_chars:
            safe_texts.append(t[:max_chars])
        else:
            safe_texts.append(t)

    res = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=safe_texts
    )

    return [d.embedding for d in res.data]


def store_embeddings(conn, rows):

    sql = """
        INSERT INTO embeddings (url, title, text, embedding)
        VALUES (%s, %s, %s, %s)
    """

    with conn.cursor() as cur:
        cur.executemany(sql, rows)

    conn.commit()


def load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def process_json(json_file: str):

    data = load_json(json_file)

    total = 0

    with psycopg.connect(DATABASE_URL) as conn:

        for item in data:

            url = item.get("url", "")
            title = item.get("title", "")
            text = item.get("text", "")

            if not text.strip():
                continue

            if len(text.strip()) < 100:
                continue

            full_doc = f"Title: {title}\nURL: {url}\n\n{text}"

            chunks = chunk_text(text)

            contextualized = []

            for chunk in chunks:

                ctx = add_context_to_chunk(full_doc, chunk)
                contextualized.append(ctx)

            embeddings = get_embeddings(contextualized)

            rows = [
                (url, title, txt, emb)
                for txt, emb in zip(contextualized, embeddings)
            ]

            store_embeddings(conn, rows)

            total += len(rows)

            print(f"Stored {len(rows)} | Total: {total}")


if __name__ == "__main__":

    process_json("parsing-python/nmbu/nmbu_data.json")
