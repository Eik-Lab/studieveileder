import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from query import get_answer

load_dotenv()

app = FastAPI(title="Studieveileder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.dittstudie.no",
        "https://dittstudie.no",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str


class CourseResponse(BaseModel):
    success: bool
    data: dict | List[dict]
    message: Optional[str] = None


@app.get("/")
def root():
    return {
        "message": "Studieveileder API",
        "endpoints": [
            "GET /api/courses",
            "GET /api/course/{kode}",
            "POST /api/chat"
        ]
    }


@app.get("/api/courses")
def get_courses():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM emner")
                data = cur.fetchall()

        return {
            "success": True,
            "data": data or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/course/{kode}")
def get_course(kode: str):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM emner WHERE emnekode = %s",
                    (kode.upper(),)
                )
                data = cur.fetchone()

        if not data:
            raise HTTPException(status_code=404, detail=f"Course {kode} not found")

        return {
            "success": True,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        answer = get_answer(request.query)

        return {"answer": answer}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
