from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configure CORS to allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("Warning: Supabase credentials not found in environment variables")
    supabase: Client = None
else:
    supabase: Client = create_client(supabase_url, supabase_key)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/example")
def get_example():
    return {"data": "This is example data from the backend"}

@app.get("/api/courses")
async def get_courses():
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured")

    try:
        response = supabase.table("emner").select("*").execute()

        if response.data:
            # Filter out empty/invalid entries
            courses = [c for c in response.data if c.get("navn") and c.get("navn") != "NMBU"]
            return {"success": True, "data": courses, "count": len(courses)}

        return {"success": True, "data": [], "count": 0}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/course/{kode}")
async def get_course(kode: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured")

    try:
        # Try exact match first
        response = supabase.table("emner").select("*").eq("emnekode", kode).maybe_single().execute()

        if response.data:
            return {"success": True, "data": response.data}

        # Try uppercase fallback
        response = supabase.table("emner").select("*").eq("emnekode", kode.upper()).maybe_single().execute()

        if response.data:
            return {"success": True, "data": response.data}

        raise HTTPException(status_code=404, detail=f"Course with code '{kode}' not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Pydantic models for chat
class ChatQuery(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(query: ChatQuery):
    """
    Handle chat queries from the academic advisor.
    This is a placeholder endpoint - integrate with your AI/RAG system here.
    """
    try:
        # TODO: Integrate with your AI/RAG system (vector database, LLM, etc.)
        # For now, returning a placeholder response

        user_query = query.query.lower()

        # Simple keyword-based responses as placeholder
        if "nmbu" in user_query:
            answer = "NMBU (Norges miljø- og biovitenskapelige universitet) er Norges universitetet for livsvitenskapene. NMBU tilbyr utdanning og forskning innen bl.a. miljø, biovitenskap, veterinærmedisin og realfag."
        elif "permisjon" in user_query:
            answer = "For å søke om permisjon fra studiet, må du sende en søknad til studieavdelingen. Du kan kontakte dem på studieveiledning@nmbu.no for mer informasjon om prosessen."
        elif "semesterregistrering" in user_query or "frist" in user_query:
            answer = "Fristen for semesterregistrering er vanligvis i midten av august for høstsemesteret og midten av januar for vårsemesteret. Sjekk StudentWeb for eksakte datoer."
        elif "timeplan" in user_query:
            answer = "Du finner din timeplan i TimeEdit. Gå til nmbu.no og søk etter 'TimeEdit' eller logg inn via StudentWeb."
        elif "bacheloroppgave" in user_query:
            answer = "Kravene til bacheloroppgaven varierer etter studieprogram. Ta kontakt med din studieveileder eller sjekk studieprogrammets nettsider for spesifikke krav og retningslinjer."
        else:
            answer = f"Takk for spørsmålet ditt om '{query.query}'. Dette er en demo-veileder under utvikling. For detaljert informasjon, kontakt studieavdelingen på studieveiledning@nmbu.no eller besøk nmbu.no."

        return ChatResponse(answer=answer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat query: {str(e)}")
