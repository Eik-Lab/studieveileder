import os
import re
from typing import List, Tuple, Optional, Dict

import psycopg
from psycopg.rows import dict_row

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")


openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=30.0,
)

conn = psycopg.connect(
    DATABASE_URL,
    row_factory=dict_row,
)
conn.autocommit = True


EMNEKODE_REGEX = re.compile(r"\b[A-ZÆØÅ]{2,4}\d{3,4}\b")


INTENT_POLICY: Dict[str, Dict[str, int | str]] = {
    "admin_rules": {"model": "gpt-4o-mini", "max_context_chars": 8000},
    "deadline_timebound": {"model": "gpt-4o-mini", "max_context_chars": 8000},
    "exam_rules_specific": {"model": "gpt-4o-mini", "max_context_chars": 8000},
    "exam_rules_general": {"model": "gpt-4o-mini", "max_context_chars": 8000},
    "conditional_rule": {"model": "gpt-4o", "max_context_chars": 10000},
    "progression_consequence": {"model": "gpt-4o", "max_context_chars": 10000},
    "comparison": {"model": "gpt-4o", "max_context_chars": 12000},
    "study_overview": {"model": "gpt-4o", "max_context_chars": 15000},
    "study_followup": {"model": "gpt-4o", "max_context_chars": 15000},
    "specific_emne": {"model": "gpt-4o", "max_context_chars": 10000},
    "concept_explanation": {"model": "gpt-4o", "max_context_chars": 8000},
    "off_topic": {"model": "none", "max_context_chars": 0},
}


def extract_emnekoder(text: str) -> List[str]:
    return list(set(EMNEKODE_REGEX.findall(text.upper())))


def fetch_all_studies() -> List[str]:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT navn FROM studier")
            rows = cur.fetchall()
        return [r["navn"] for r in rows]
    except Exception:
        return []


def fetch_emne(emnekode: str) -> Optional[dict]:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM emner WHERE emnekode = %s",
                (emnekode,),
            )
            return cur.fetchone()
    except Exception:
        return None


def match_embeddings(embedding: list, limit: int = 8) -> List[str]:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT text FROM match_embeddings(%s::vector, %s)",
                (embedding, limit),
            )
            rows = cur.fetchall()
        return [r["text"] for r in rows]
    except Exception:
        return []


def extract_study_mentions(question: str) -> List[str]:
    try:
        studies = fetch_all_studies()
        q = question.lower()
        return [s for s in studies if s.lower() in q]
    except Exception:
        return []


def classify_exam_failure(q: str) -> str:
    if any(w in q for w in ["hvor mange", "antall", "maks", "grense"]):
        return "exam_rules_specific"
    return "exam_rules_general"


def classify_intent(
    question: str,
    emnekoder: List[str],
    studies: List[str],
) -> str:
    q = question.lower()

    if any(w in q for w in ["vær", "mat", "politikk", "jobb", "lønn"]):
        return "off_topic"

    if any(w in q for w in ["frist", "dato", "innen", "senest"]):
        return "deadline_timebound"

    if any(w in q for w in ["permisjon", "timeplan", "timeedit", "studentweb"]):
        return "admin_rules"

    if any(w in q for w in ["må jeg", "kan jeg", "er det krav", "forutsetter"]):
        return "conditional_rule"

    if any(w in q for w in ["hva skjer hvis", "konsekvens", "forsinker", "progresjon"]):
        return "progression_consequence"

    if any(w in q for w in ["forskjell", "vs", "sammenlign"]):
        return "comparison"

    if any(w in q for w in ["stryker", "konte", "kontinuasjon"]):
        return classify_exam_failure(q)

    if studies:
        return "study_overview"

    if emnekoder:
        return "specific_emne"

    if any(w in q for w in ["hva er", "forklar", "betyr"]):
        return "concept_explanation"

    return "off_topic"


def fetch_rules_context(query: str) -> List[str]:
    try:
        emb = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
        ).data[0].embedding

        matches = match_embeddings(emb, 10)
        return [f"[REGLER]\n{text}" for text in matches]
    except Exception:
        return []


def fetch_emne_block(emnekode: str) -> Optional[str]:
    r = fetch_emne(emnekode)
    if not r:
        return None

    return "\n".join([
        "[EMNE]",
        f"Emnekode: {r['emnekode']}",
        f"Navn: {r['navn']}",
        f"Studiepoeng: {r['studiepoeng']}",
        f"Fakultet: {r['fakultet']}",
        f"Semester: {r['semester']}",
        f"Språk: {r['språk']}",
        "",
        "[INNHOLD]",
        f"Dette lærer du: {r.get('dette_lærer_du')}",
        f"Forkunnskaper: {r.get('forkunnskaper')}",
        f"Læringsaktiviteter: {r.get('læringsaktiviteter')}",
        "",
        "[VURDERING]",
        f"Vurderingsordning: {r.get('vurderingsordning')}",
        f"Obligatoriske aktiviteter: {r.get('obligatoriske_aktiviteter')}",
        "",
        "[ANNET]",
        f"Fortrinnsrett: {r.get('fortrinnsrett')}",
        f"Merknader: {r.get('merknader')}",
    ])


def trim_context(blocks: List[str], max_chars: int) -> str:
    out = []
    total = 0

    for b in blocks:
        if total + len(b) > max_chars:
            if len(out) == 0:
                out.append(b[:max_chars])
            break
        out.append(b)
        total += len(b)

    return "\n\n".join(out)


def build_context(question: str) -> Tuple[str, str, Dict[str, int | str]]:
    emnekoder = extract_emnekoder(question)
    studies = extract_study_mentions(question)
    intent = classify_intent(question, emnekoder, studies)

    blocks: List[str] = []

    if intent in {
        "admin_rules",
        "deadline_timebound",
        "exam_rules_general",
        "exam_rules_specific",
        "conditional_rule",
        "progression_consequence",
    }:
        blocks.extend(fetch_rules_context(question))

    if intent == "specific_emne":
        for e in emnekoder:
            b = fetch_emne_block(e)
            if b:
                blocks.append(b)

    policy = INTENT_POLICY[intent]
    context = trim_context(blocks, policy["max_context_chars"])

    return context, intent, policy


SYSTEM_PROMPT = """
Du er en studieveileder ved et universitet.

Regler:
- Bruk kun informasjonen i konteksten
- Aldri anta studie, kull eller spesialisering
- Ved betingede spørsmål: forklar hva svaret avhenger av
- Ved frister: oppgi kun det som eksplisitt står
- Hvis informasjon mangler: si det tydelig
- Norsk språk
"""


def get_answer(question: str) -> str:
    try:
        context, intent, policy = build_context(question)

        if intent == "off_topic":
            return "Jeg kan kun svare på spørsmål om studier, emner og regler ved universitetet."

        if not context:
            return "Jeg finner ingen relevant informasjon i regelverket til å svare på dette."

        r = openai_client.chat.completions.create(
            model=policy["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"KONTEKST:\n{context}\n\nSPØRSMÅL:\n{question}"
                },
            ],
        )

        return r.choices[0].message.content.strip()

    except Exception as e:
        return f"Feil: {str(e)}"


def main():
    print("Studieveileder CLI (skriv 'exit')")

    while True:
        q = input("\n> ").strip()

        if q.lower() in {"exit", "quit"}:
            break

        print("\n--- SVAR ---")
        print(get_answer(q))


if __name__ == "__main__":
    main()