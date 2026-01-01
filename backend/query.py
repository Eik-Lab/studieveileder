import os
import re
from typing import List
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)

EMNEKODE_REGEX = re.compile(r"\b[A-Z]{2,4}\d{3,4}\b")

MAX_CONTEXT_CHARS = 8000


def get_embedding(text: str) -> List[float]:
    r = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return r.data[0].embedding


def extract_emnekoder(text: str) -> List[str]:
    return list(set(EMNEKODE_REGEX.findall(text.upper())))


def classify_intent(question: str, emnekoder: List[str]) -> str:
    q = question.lower()

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


def fetch_embeddings(query: str, k: int) -> List[str]:
    embedding = get_embedding(query)
    r = supabase.rpc(
        "match_embeddings",
        {
            "query_embedding": embedding,
            "match_count": k,
        },
    ).execute()

    return [
        f"[KILDE]\n{row['content']}"
        for row in (r.data or [])
    ]


def trim_context(blocks: List[str]) -> str:
    out = []
    total = 0
    for b in blocks:
        if total + len(b) > MAX_CONTEXT_CHARS:
            break
        out.append(b)
        total += len(b)
    return "\n\n".join(out)


def build_context(question: str) -> tuple[str, str]:
    emnekoder = extract_emnekoder(question)
    intent = classify_intent(question, emnekoder)

    blocks = []

    if emnekoder:
        blocks.extend(fetch_emner(emnekoder))
        blocks.extend(fetch_embeddings(question, k=3))
    else:
        blocks.extend(fetch_embeddings(question, k=5))

    return trim_context(blocks), intent


SYSTEM_PROMPT = """
Du er en studieveileder ved et universitet.

GRUNNREGEL:
Svar primært basert på informasjonen du får i konteksten.

UNNTAK – KONSEPTFORKLARING:
Hvis brukeren ber om å forklare et faglig konsept,
kan du bruke generell, allment anerkjent fagkunnskap
FORUTSATT AT:
- konseptet er tydelig relevant for emnet/emnene i konteksten
- forklaringen er nøktern, presis og faglig korrekt
- du ikke spekulerer eller går utenfor emnets domene

KRAV:
- Skill eksplisitt mellom:
  • informasjon fra konteksten
  • generell fagkunnskap
- Hvis spørsmålet ikke er faglig relevant for emnet:
  si tydelig at det faller utenfor

FORBUD:
- Ikke svar på urelaterte temaer
- Ikke improviser eller gjett
- Ikke utvid emnets omfang

SPRÅK:
- Norsk
- Strukturert og presist
"""


def get_answer(question: str) -> str:
    context, intent = build_context(question)

    user_instruction = (
        f"Tilgjengelig informasjon:\n\n{context}\n\n"
        f"Spørsmål:\n{question}\n\n"
        "Hvis du bruker generell fagkunnskap, merk dette eksplisitt."
    )

    r = openai_client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_instruction},
        ],
    )

    return r.choices[0].message.content.strip()
