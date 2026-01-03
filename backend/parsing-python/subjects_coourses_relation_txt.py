import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

load_dotenv()

TXT_FOLDER = "parsing-python/studieplaner/studieplaner_txt"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

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
            {"role": "user", "content": user_text[:12000]}
        ],
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

def get_studie_id(navn, study_type):
    res = supabase.table("studier").upsert(
        {"navn": navn, "type": study_type},
        on_conflict="navn"
    ).execute()
    return res.data[0]["studie_id"]

def get_spes_id(studie_id, navn):
    res = supabase.table("spesialiseringer").upsert(
        {"studie_id": studie_id, "navn": navn},
        on_conflict="studie_id,navn"
    ).execute()
    return res.data[0]["spesialisering_id"]

def get_emne_id(emnekode):
    res = supabase.table("emner").select("id").eq(
        "emnekode", emnekode
    ).execute()
    return res.data[0]["id"] if res.data else None

def insert_fag(studie_id, spes_id, studieaar, fag):
    emne_id = get_emne_id(fag["emnekode"])
    if not emne_id:
        return

    supabase.table("studiefag").insert({
        "studie_id": studie_id,
        "spesialisering_id": spes_id,
        "emne_id": emne_id,
        "studieaar": studieaar,
        "semester": fag["semester"],
        "obligatorisk": fag["obligatorisk"],
        "kommentar": fag.get("kommentar")
    }).execute()

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
            f"{filename}::{spes['navn']}"
        )

        for block in data["struktur"]:
            for fag in block["fag"]:
                insert_fag(
                    studie_id,
                    spes_id,
                    block["studieaar"],
                    fag
                )

def main():
    files = [f for f in os.listdir(TXT_FOLDER) if f.lower().endswith(".txt")]
    print(f"Fant {len(files)} studieplaner")

    for file in files:
        try:
            print(f"→ Leser {file}")
            process_txt(os.path.join(TXT_FOLDER, file))
        except Exception as e:
            print(f"[ERROR] {file}: {e}")

if __name__ == "__main__":
    main()
