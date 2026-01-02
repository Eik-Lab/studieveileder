import os
import re
from typing import List, Tuple
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)

SESSION = {
    "current_study": None
}

EMNEKODE_REGEX = re.compile(r"\b[A-ZÆØÅ]{2,4}\d{3,4}\b")
MAX_CONTEXT_CHARS = 4000


def extract_emnekoder(text: str) -> List[str]:
    return list(set(EMNEKODE_REGEX.findall(text.upper())))


def extract_study_mentions(question: str) -> List[str]:
    r = supabase.table("studier").select("navn").execute()
    studies = [s["navn"] for s in r.data or []]
    q = question.lower()
    return [s for s in studies if s.lower() in q]


def classify_intent(question: str, emnekoder: List[str], studies: List[str]) -> str:
    q = question.lower()
    if studies:
        return "study_overview"
    if any(w in q for w in ["hva er", "forklar", "betyr", "konsept", "teori"]):
        return "concept_explanation"
    if emnekoder:
        return "specific_emne"
    return "general"


def fetch_emner(emnekoder: List[str]) -> List[str]:
    if not emnekoder:
        return []
    r = (
        supabase.table("emner")
        .select("*")
        .in_("emnekode", emnekoder)
        .execute()
    )
    blocks = []
    for e in r.data or []:
        blocks.append(
            "\n".join(
                [
                    "[EMNE]",
                    f"Emnekode: {e.get('emnekode')}",
                    f"Navn: {e.get('navn')}",
                    f"Forkunnskaper: {e.get('forkunnskapskrav')}",
                    f"Vurdering: {e.get('vurdering')}",
                ]
            )
        )
    return blocks


def fetch_study_structure(study_name: str) -> List[str]:
    blocks = []
    studie = (
        supabase.table("studier")
        .select("studie_id, navn, type")
        .eq("navn", study_name)
        .single()
        .execute()
        .data
    )
    if not studie:
        return []
    studie_id = studie["studie_id"]
    spes = (
        supabase.table("spesialiseringer")
        .select("spesialisering_id, navn")
        .eq("studie_id", studie_id)
        .execute()
        .data
    )
    if not spes:
        spes = [{"spesialisering_id": None, "navn": "Felles emner"}]
    for s in spes:
        fag = (
            supabase.table("studiefag")
            .select(
                "studieaar, semester, obligatorisk, kommentar, emner(emnekode, navn)"
            )
            .eq("studie_id", studie_id)
            .eq("spesialisering_id", s["spesialisering_id"])
            .order("studieaar")
            .execute()
            .data
        )
        lines = [
            "[STUDIE]",
            f"Studie: {studie['navn']} ({studie['type']})",
            f"Spesialisering: {s['navn']}",
        ]
        for f in fag or []:
            e = f["emner"]
            lines.append(
                f"- År {f['studieaar']} | {e['emnekode']} {e['navn']} ({f['semester']}, {'obligatorisk' if f['obligatorisk'] else 'valgfritt'})"
            )
        blocks.append("\n".join(lines))
    return blocks


def fetch_embeddings(query: str, k: int = 6) -> List[str]:
    try:
        emb = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding
        r = supabase.rpc(
            "match_embeddings",
            {"query_embedding": emb, "match_count": k},
        ).execute()
        blocks = []
        for row in r.data or []:
            blocks.append(f"[KILDE: {row.get('source')}]\n{row.get('text')}")
        return blocks
    except Exception:
        return []


def trim_context(blocks: List[str]) -> str:
    out, total = [], 0
    for b in blocks:
        if total + len(b) > MAX_CONTEXT_CHARS:
            break
        out.append(b)
        total += len(b)
    return "\n\n".join(out)


def build_context(question: str) -> Tuple[str, str]:
    emnekoder = extract_emnekoder(question)
    studies = extract_study_mentions(question)
    if studies:
        SESSION["current_study"] = studies[0]
    intent = classify_intent(question, emnekoder, studies)
    blocks = []
    if intent == "study_overview":
        for s in studies:
            blocks.extend(fetch_study_structure(s))
    elif SESSION["current_study"]:
        blocks.extend(fetch_study_structure(SESSION["current_study"]))
        intent = "study_followup"
    elif emnekoder:
        blocks.extend(fetch_emner(emnekoder))
        blocks.extend(fetch_embeddings(question, k=4))
    else:
        blocks.extend(fetch_embeddings(question, k=6))
    return trim_context(blocks), intent


SYSTEM_PROMPT = """
Du er en studieveileder ved et universitet.

Hvis spørsmålet handler om et STUDIE:
- List spesialiseringer dersom de finnes
- Forklar hvilke fag som inngår
- Skill tydelig mellom fellesemner og spesialiseringsemner

Hvis dette er et OPPFØLGINGSSPØRSMÅL:
- Anta at brukeren refererer til samme studie som tidligere
- Ikke bytt kontekst
- Ikke bruk informasjon fra andre studier

Regler:
- Bruk kun informasjonen i konteksten
- Ikke gjett eller improviser
- Bruk emnekode og emnenavn når fag omtales
- Norsk språk

Hvis du får spørsmål som krever spesifikke handlinger, må du fortelle brukeren at de skal ta kontakt med studieveileder for ditt fakultet.
"""


def get_answer(question: str) -> str:
    context, intent = build_context(question)
    user_prompt = (
        f"KONTEKST:\n{context}\n\n"
        f"SPØRSMÅL:\n{question}\n\n"
        "Svar kun basert på konteksten."
    )
    r = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return r.choices[0].message.content.strip()


def main():
    print("Studieveileder CLI (skriv 'exit')")
    while True:
        q = input("\n> ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        if not q:
            continue
        try:
            print("\n--- SVAR ---")
            print(get_answer(q))
        except Exception as e:
            print(f"Feil: {e}")


if __name__ == "__main__":
    main()
