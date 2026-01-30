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

CHUNK_SIZE = 300


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

            if buffer:
                chunks.append(buffer.strip())

            buffer = para

    if buffer:
        chunks.append(buffer.strip())

    return chunks


def is_good_chunk(text: str) -> bool:

    if len(text) < 80:
        return False

    if len(re.findall(r"[a-zA-ZæøåÆØÅ]", text)) < 40:
        return False

    if text.count(" ") < 10:
        return False

    return True


def get_embeddings(
    texts: List[str],
    max_chars: int = 6000
) -> List[List[float]]:

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

            if len(text.strip()) < 150:
                continue

            chunks = chunk_text(text)

            valid_chunks = []

            for chunk in chunks:

                if not is_good_chunk(chunk):
                    continue

                valid_chunks.append(chunk)

            if not valid_chunks:
                continue

            embeddings = get_embeddings(valid_chunks)

            rows = [
                (url, title, txt, emb)
                for txt, emb in zip(valid_chunks, embeddings)
            ]

            store_embeddings(conn, rows)

            total += len(rows)

            print(f"Stored {len(rows)} | Total: {total}")


if __name__ == "__main__":

    process_json("parsing-python/nmbu/nmbu_data.json")
