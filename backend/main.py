import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
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

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)


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
    """Get all courses from the database"""
    try:
        response = supabase.table("emner").select("*").execute()

        return {
            "success": True,
            "data": response.data or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/course/{kode}")
def get_course(kode: str):
    """Get a specific course by its course code (emnekode)"""
    try:
        response = (
            supabase.table("emner")
            .select("*")
            .eq("emnekode", kode.upper())
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail=f"Course {kode} not found")

        return {
            "success": True,
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat(request: ChatRequest):
    """Chat endpoint that uses RAG to answer questions about courses"""
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
