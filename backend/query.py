import os
import re
from typing import List, Tuple, Optional
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
    "current_study": None,
    "current_emne": None
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


def classify_exam_failure(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["hvor mange", "antall", "maks", "grense"]):
        return "exam_rules_specific"
    return "exam_rules_general"


def classify_intent(question: str, emnekoder: List[str], studies: List[str]) -> str:
    q = question.lower()
    if any(w in q for w in ["stryker", "strøket", "ikke består", "konte", "kontinuasjon", "ny eksamen"]):
        return classify_exam_failure(question)
    if len(studies) >= 2:
        return "study_comparison"
    if studies:
        return "study_overview"
    if emnekoder:
        return "specific_emne"
    if any(w in q for w in ["hva er", "forklar", "betyr", "konsept", "teori"]):
        return "concept_explanation"
    return "general"


def fetch_emne_block(emnekode: str) -> Optional[str]:
    r = (
        supabase.table("emner")
        .select("*")
        .eq("emnekode", emnekode)
        .single()
        .execute()
        .data
    )
    if not r:
        return None
    return "\n".join(
        [
            "[EMNE]",
            f"Emnekode: {r.get('emnekode')}",
            f"Navn: {r.get('navn')}",
            f"Forkunnskaper: {r.get('forkunnskapskrav')}",
            f"Vurdering: {r.get('vurdering')}",
        ]
    )


def fetch_exam_rules_context(query: str) -> List[str]:
    try:
        emb = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding

        r = supabase.rpc(
            "match_embeddings",
            {
                "query_embedding": emb,
                "match_count": 5
            },
        ).execute()

        blocks = []
        for row in r.data or []:
            src = (row.get("source") or "").lower()
            if any(k in src for k in ["konte", "eksamen", "vurdering"]):
                blocks.append(f"[REGLER]\n{row.get('text')}")
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


def build_context(question: str) -> Tuple[str, str, Optional[str]]:
    emnekoder = extract_emnekoder(question)
    studies = extract_study_mentions(question)
    intent = classify_intent(question, emnekoder, studies)

    if emnekoder:
        SESSION["current_emne"] = emnekoder[0]
    if studies:
        SESSION["current_study"] = studies[0]

    blocks = []

    if intent in {"exam_rules_general", "exam_rules_specific"}:
        emne = emnekoder[0] if emnekoder else SESSION["current_emne"]
        if not emne:
            return "", "clarify_emne", None
        emne_block = fetch_emne_block(emne)
        if emne_block:
            blocks.append(emne_block)
        blocks.extend(fetch_exam_rules_context(question))
        return trim_context(blocks), intent, emne

    if intent == "study_overview":
        for s in studies:
            blocks.extend(fetch_study_structure(s))

    elif intent == "specific_emne":
        for e in emnekoder:
            block = fetch_emne_block(e)
            if block:
                blocks.append(block)

    elif SESSION["current_study"]:
        blocks.extend(fetch_study_structure(SESSION["current_study"]))
        intent = "study_followup"

    return trim_context(blocks), intent, None


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


SYSTEM_PROMPT = """
Du er en studieveileder ved et universitet.

Regler:
- Bruk kun informasjonen i konteksten
- Ikke anta studie eller spesialisering uten grunnlag
- Bruk emnekode og emnenavn eksplisitt
- Ved eksamens- og konte-spørsmål: svar kun ut fra reglene i konteksten
- Hvis informasjon mangler, si det tydelig
- Norsk språk
"""


def get_answer(question: str) -> str:
    context, intent, _ = build_context(question)

    if intent == "clarify_emne":
        return "Hvilket emne gjelder spørsmålet?"

    user_prompt = (
        f"KONTEKST:\n{context}\n\n"
        f"SPØRSMÅL:\n{question}\n\n"
        "Svar kun basert på konteksten over."
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
