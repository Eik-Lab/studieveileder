import os
import re
import json
import time
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
    raise ValueError("Missing required environment variables")

client = OpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SUBJECT_FOLDER = "parsing-python/subject_contents"

FIELDS = {
    "navn": r"^(.+?)\s*\|\s*NMBU\s*\|\s*NMBU",
    "studiepoeng": r"Studiepoeng:\s*(.+)",
    "semester": r"Undervisningstermin:\s*(.+)",
    "fakultet": r"Ansvarlig fakultet:\s*(.+)",
    "underviser": r"Emneansvarlig:\s*(.+)",
    "språk": r"Undervisningens språk:\s*(.+)",
    "antall_plasser": r"Antall plasser:\s*(.+)",
    "dette_lærer_du": r"Dette lærer du([\s\S]+?)(?:Læringsaktiviteter|Pensum|Forutsatte forkunnskaper)",
    "forkunnskaper": r"Forutsatte forkunnskaper[:\s]*([\s\S]+?)(?:Vurderingsordning|Obligatorisk|Merknader|Undervisningstider|$)",
    "læringsaktiviteter": r"Læringsaktiviteter([\s\S]+?)(?:Læringsstøtte|Pensum|Forutsatte forkunnskaper)",
    "vurderingsordning": r"Vurderingsordning, hjelpemiddel og eksamen([\s\S]+?)(?:Om bruk av KI|Sensorordning|Obligatorisk aktivitet)",
    "obligatoriske_aktiviteter": r"Obligatorisk aktivitet\s*([\s\S]+?)(?:Merknader|Undervisningstimer|Opptakskrav|$)",
    "merknader": r"Merknader\s*([\s\S]+?)(?:Undervisningstider|Opptakskrav|$)",
    "fortrinnsrett": r"Fortrinnsrett\s*([\s\S]+?)(?:Opptakskrav|Merknader|$)",
}

SYSTEM_PROMPT = """
Du er studieplanredaktør ved NMBU.

Oppgave:
Forbedre og presisere eksisterende studieplantekst slik at innholdet blir klarere, mer presist og lettere å forstå for studenter i praksis.

Regler:
- Ikke introduser ny faglig informasjon
- Ikke referer til nivå, grad eller vanskelighetsgrad
- Ingen pedagogiske klisjeer eller forenklinger
- Forbedre språk, presisjon og flyt i alle felt

Unntak – feltet "dette_lærer_du":
- Kan konkretiseres med presise faglige formuleringer
- Kan beskrive typiske aktiviteter, problemstillinger eller anvendelser
- Eventuelle eksempler må være realistiske og tydelig forankret i originalteksten

Begrensninger:
- All presisering må være klart forankret i eksisterende tekst
- Ikke utvid omfang, mål eller ambisjonsnivå

Output:
- Returner kun gyldig JSON
- Behold eksakt samme struktur og nøkler som input
"""

def clean_text(text):
    if not text:
        return None
    text = re.sub(r"\n\s*\n+", "\n", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize_integer(value):
    if not value:
        return None
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None

def normalize_semester(value):
    if not value:
        return None

    v = value.lower()

    if "høst" in v and "vår" in v:
        return "Hele året"
    if "høst" in v:
        return "Høst"
    if "vår" in v:
        return "Vår"

    return None

def parse_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    data = {"emnekode": os.path.splitext(os.path.basename(filepath))[0]}

    for key, pattern in FIELDS.items():
        m = re.search(pattern, content, re.MULTILINE)
        data[key] = clean_text(m.group(1)) if m else None

    return data

def strip_nulls(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}

def extract_json(text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in model output")
    return json.loads(match.group())

def improve_with_openai(data: dict) -> dict:
    payload = strip_nulls(data)
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )
    return extract_json(response.output_text)

def format_eta(seconds):
    if seconds < 0:
        return "–"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"

def main():
    files = [f for f in os.listdir(SUBJECT_FOLDER) if f.endswith(".txt")]
    total = len(files)
    processed = 0
    skipped = 0
    failed = 0
    start_time = time.time()

    print(f"Starter prosessering av {total} emner")

    for idx, filename in enumerate(files, start=1):
        t0 = time.time()
        try:
            data = parse_file(os.path.join(SUBJECT_FOLDER, filename))

            meaningful_fields = sum(
                1 for v in data.values() if isinstance(v, str) and len(v) > 20
            )
            if meaningful_fields < 3:
                skipped += 1
                continue

            data = improve_with_openai(data)

            data["studiepoeng"] = normalize_integer(data.get("studiepoeng"))
            data["antall_plasser"] = normalize_integer(data.get("antall_plasser"))
            data["semester"] = normalize_semester(data.get("semester"))

            supabase.table("emner").upsert(
                data,
                on_conflict="emnekode",
            ).execute()

            processed += 1

        except Exception as e:
            failed += 1
            print(f"[ERROR] {filename}: {e}")

        elapsed = time.time() - start_time
        avg_time = elapsed / max(1, idx)
        eta = avg_time * (total - idx)

        print(
            f"[{idx}/{total}] "
            f"ok={processed} skip={skipped} fail={failed} "
            f"ETA {format_eta(eta)}"
        )

        time.sleep(0.15)

    total_time = time.time() - start_time
    print(
        f"Ferdig på {format_eta(total_time)} | "
        f"ok={processed} skip={skipped} fail={failed}"
    )

if __name__ == "__main__":
    main()
