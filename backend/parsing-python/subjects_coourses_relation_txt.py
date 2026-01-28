import os
import json
import re
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TXT_FOLDER = "parsing-python/studieplaner/studieplaner_txt"

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
conn.autocommit = True


SYSTEM_PROMPT_STEP_1 = """
Du er studieplananalytiker ved NMBU.

Oppgave:
Identifiser ALLE spesialiseringer i studieplanen.

Regler:
- Finn alle spesialiseringer eksplisitt nevnt
- Del teksten slik at hver spesialisering får sin EGEN tekstblokk
- Ikke tolk fag eller studieår
- Ikke utelat tekst

Returner KUN gyldig JSON i dette formatet:

{
  "studie": "...",
  "type": "...",
  "kull": 2025,
  "spesialiseringer": [
    {
      "navn": "...",
      "tekst": "..."
    }
  ]
}
"""


SYSTEM_PROMPT_STEP_2 = """
Du er studieplananalytiker ved NMBU.

Oppgave:
Strukturer fag for ÉN spesialisering.

Regler:
- Bruk kun teksten du får
- Ikke utelat fag
- Studieår bestemmes ut fra årstall i planen
- Studieår starter på 1

Semesterverdier:
aug | jan | vår | høst

Returner KUN gyldig JSON:

{
  "struktur": [
    {
      "studieaar": 1,
      "fag": [
        {
          "emnekode": "...",
          "semester": "...",
          "obligatorisk": true,
          "kommentar": null
        }
      ]
    }
  ]
}
"""


def read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_json(text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("Fant ingen JSON i OpenAI-output")
    return json.loads(match.group())


def openai_call(system_prompt: str, user_text: str, filename: str) -> dict:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text[:12000]},
        ],
        timeout=60,
    )

    raw = response.output_text.strip()

    if not raw:
        raise ValueError("Tom OpenAI-respons")

    try:
        return extract_json(raw)
    except Exception:
        print(f"\n--- OPENAI RAW OUTPUT ({filename}) ---\n")
        print(raw[:4000])
        print("\n--- SLUTT ---\n")
        raise


def get_cursor():
    return conn.cursor()


def get_studie_id(navn, study_type):
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO studier (navn, type)
            VALUES (%s, %s)
            ON CONFLICT (navn)
            DO UPDATE SET type = EXCLUDED.type
            RETURNING studie_id
            """,
            (navn, study_type),
        )

        return cur.fetchone()["studie_id"]


def get_spes_id(studie_id, navn):
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO spesialiseringer (studie_id, navn)
            VALUES (%s, %s)
            ON CONFLICT (studie_id, navn)
            DO NOTHING
            RETURNING spesialisering_id
            """,
            (studie_id, navn),
        )

        res = cur.fetchone()

        if res:
            return res["spesialisering_id"]

        cur.execute(
            """
            SELECT spesialisering_id
            FROM spesialiseringer
            WHERE studie_id = %s AND navn = %s
            """,
            (studie_id, navn),
        )

        return cur.fetchone()["spesialisering_id"]


def get_emne_id(emnekode):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM emner
            WHERE emnekode = %s
            """,
            (emnekode,),
        )

        res = cur.fetchone()

        return res["id"] if res else None


def insert_fag(studie_id, spes_id, studieaar, fag):
    emne_id = get_emne_id(fag["emnekode"])

    if not emne_id:
        return

    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO studiefag (
              studie_id,
              spesialisering_id,
              emne_id,
              studieaar,
              semester,
              obligatorisk,
              kommentar
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                studie_id,
                spes_id,
                emne_id,
                studieaar,
                fag["semester"],
                fag["obligatorisk"],
                fag.get("kommentar"),
            ),
        )


def process_txt(path: str):
    filename = os.path.basename(path)
    text = read_txt(path)

    doc = openai_call(SYSTEM_PROMPT_STEP_1, text, filename)

    studie_id = get_studie_id(doc["studie"], doc["type"])

    for spes in doc["spesialiseringer"]:
        spes_id = get_spes_id(studie_id, spes["navn"])

        data = openai_call(
            SYSTEM_PROMPT_STEP_2,
            spes["tekst"],
            f"{filename}::{spes['navn']}",
        )

        for block in data["struktur"]:
            for fag in block["fag"]:
                insert_fag(
                    studie_id,
                    spes_id,
                    block["studieaar"],
                    fag,
                )


def main():
    files = [
        f for f in os.listdir(TXT_FOLDER)
        if f.lower().endswith(".txt")
    ]

    print(f"Fant {len(files)} studieplaner")

    for file in files:
        try:
            print(f"→ Leser {file}")
            process_txt(os.path.join(TXT_FOLDER, file))
        except Exception as e:
            print(f"[ERROR] {file}: {e}")


if __name__ == "__main__":
    main()
