import os
import re
from typing import List, Tuple, Optional, Dict

import psycopg
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=30.0,
)

DATABASE_URL = os.getenv("DATABASE_URL")


SESSION = {
    "current_study": None,
    "current_emne": None,
}


EMNEKODE_REGEX = re.compile(r"\b[A-ZÆØÅ]{2,4}\d{3,4}\b")


INTENT_POLICY: Dict[str, Dict[str, int | str]] = {
    "admin_rules": {"model": "gpt-4o-mini", "max_context_chars": 3000},
    "deadline_timebound": {"model": "gpt-4o-mini", "max_context_chars": 3000},
    "exam_rules_specific": {"model": "gpt-4o-mini", "max_context_chars": 2500},
    "exam_rules_general": {"model": "gpt-4o-mini", "max_context_chars": 3000},
    "conditional_rule": {"model": "gpt-4o", "max_context_chars": 5000},
    "progression_consequence": {"model": "gpt-4o", "max_context_chars": 5000},
    "comparison": {"model": "gpt-4o", "max_context_chars": 6000},
    "study_overview": {"model": "gpt-4o", "max_context_chars": 7000},
    "study_followup": {"model": "gpt-4o", "max_context_chars": 7000},
    "specific_emne": {"model": "gpt-4o", "max_context_chars": 5000},
    "concept_explanation": {"model": "gpt-4o", "max_context_chars": 3000},
    "off_topic": {"model": "none", "max_context_chars": 0},
}


def extract_emnekoder(text: str) -> List[str]:
    return list(set(EMNEKODE_REGEX.findall(text.upper())))


def extract_study_mentions(question: str) -> List[str]:

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT navn FROM studier")
                rows = cur.fetchall()

        studies = [r[0] for r in rows]
        q = question.lower()

        return [s for s in studies if s.lower() in q]

    except Exception:
        return []


def classify_exam_failure(q: str) -> str:

    if any(w in q for w in ["hvor mange", "antall", "maks", "grense"]):
        return "exam_rules_specific"

    return "exam_rules_general"


def classify_intent(question: str, emnekoder: List[str], studies: List[str]) -> str:

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


def rerank_chunks(query: str, docs: List[str], k: int = 8) -> List[str]:

    numbered = "\n\n".join(
        [f"{i+1}. {d[:800]}" for i, d in enumerate(docs)]
    )

    prompt = f"""
You are ranking retrieved documents for relevance.

Query:
{query}

Documents:
{numbered}

Return the numbers of the {k} most relevant documents
in descending relevance order.
Only return a comma-separated list of numbers.
Example: 3,1,5,2
"""

    r = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a relevance ranker."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    order = r.choices[0].message.content.strip()

    try:
        indices = [
            int(x.strip()) - 1
            for x in order.split(",")
            if x.strip().isdigit()
        ]

        ranked = [docs[i] for i in indices if i < len(docs)]

        return ranked[:k]

    except Exception:
        return docs[:k]


def fetch_rules_context(query: str) -> List[str]:

    try:
        emb = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
        ).data[0].embedding

        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT text
                    FROM embeddings
                    ORDER BY embedding <=> %s
                    LIMIT 20
                    """,
                    (emb,),
                )

                rows = cur.fetchall()

        docs = [r[0] for r in rows]

        if not docs:
            return []

        reranked = rerank_chunks(query, docs)

        return [f"[REGLER]\n{d}" for d in reranked]

    except Exception:
        return []


def fetch_emne_block(emnekode: str) -> Optional[str]:

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:

                cur.execute(
                    "SELECT * FROM emner WHERE emnekode = %s",
                    (emnekode,),
                )

                r = cur.fetchone()

        if not r:
            return None

        cols = [d.name for d in cur.description]
        data = dict(zip(cols, r))

        return "\n".join([
            "[EMNE]",
            f"Emnekode: {data['emnekode']}",
            f"Navn: {data['navn']}",
            f"Studiepoeng: {data['studiepoeng']}",
            f"Fakultet: {data['fakultet']}",
            f"Semester: {data['semester']}",
            f"Språk: {data['språk']}",
            "",
            "[INNHOLD]",
            f"Dette lærer du: {data.get('dette_lærer_du')}",
            f"Forkunnskaper: {data.get('forkunnskaper')}",
            f"Læringsaktiviteter: {data.get('læringsaktiviteter')}",
            "",
            "[VURDERING]",
            f"Vurderingsordning: {data.get('vurderingsordning')}",
            f"Obligatoriske aktiviteter: {data.get('obligatoriske_aktiviteter')}",
            "",
            "[ANNET]",
            f"Fortrinnsrett: {data.get('fortrinnsrett')}",
            f"Merknader: {data.get('merknader')}",
        ])

    except Exception:
        return None


def trim_context(blocks: List[str], max_chars: int) -> str:

    out = []
    total = 0

    for b in blocks:

        if total + len(b) > max_chars:
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

    return trim_context(blocks, policy["max_context_chars"]), intent, policy


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
                    "content": f"KONTEKST:\n{context}\n\nSPØRSMÅL:\n{question}",
                },
            ],
        )

        return r.choices[0].message.content.strip()

    except Exception as e:
        return f"Beklager, det oppstod en feil ved behandling av spørsmålet: {str(e)}"


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
