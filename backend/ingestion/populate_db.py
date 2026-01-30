import os
import re
import json
import time
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg
from openai import OpenAI
from dotenv import load_dotenv


MAX_WORKERS = 6
SUBJECT_FOLDER = "parsing-python/subject_contents"


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DATABASE_URL or not OPENAI_API_KEY:
    raise ValueError("Missing required environment variables")

client = OpenAI(api_key=OPENAI_API_KEY)


FIELDS = {
    "navn": r"^(.+?)\s*\|\s*NMBU\s*\|\s*NMBU",
    "studiepoeng": r"Studiepoeng:\s*(.+)",
    "semester": r"Undervisnings- og vurderingsperiode:\s*(.+)",
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
Forbedre og presisere eksisterende studieplantekst.

Regler:
- Ikke introduser ny informasjon
- Ikke referer til nivå
- Forbedre språk

Output:
- Returner kun gyldig JSON
- Behold samme struktur
"""


def clean_text(text: Optional[str]) -> Optional[str]:

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


def normalize_float(value):

    if not value:
        return None

    m = re.search(r"\d+(?:[.,]\d+)?", value)

    if not m:
        return None

    return float(m.group().replace(",", "."))


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


def parse_file(filepath: str) -> dict:

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    data = {
        "emnekode": os.path.splitext(os.path.basename(filepath))[0]
    }

    for key, pattern in FIELDS.items():

        m = re.search(pattern, content, re.MULTILINE)

        data[key] = clean_text(m.group(1)) if m else None

    return data


def extract_json(text: str) -> dict:

    match = re.search(r"\{[\s\S]*\}", text)

    if not match:
        raise ValueError("No JSON found")

    return json.loads(match.group())


def improve_with_openai(data: dict) -> dict:

    for _ in range(3):

        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
                ],
                timeout=60,
            )

            return extract_json(response.output_text)

        except Exception:
            time.sleep(5)

    raise RuntimeError("OpenAI failed")


def is_done(conn, emnekode: str) -> bool:

    with conn.cursor() as cur:

        cur.execute(
            "SELECT processed_at FROM emner WHERE emnekode = %s",
            (emnekode,)
        )

        row = cur.fetchone()

        return row is not None and row[0] is not None


def update_emne(conn, data: dict):

    sql = """
        INSERT INTO emner (
            emnekode,
            navn,
            studiepoeng,
            semester,
            fakultet,
            underviser,
            språk,
            antall_plasser,
            dette_lærer_du,
            forkunnskaper,
            læringsaktiviteter,
            vurderingsordning,
            obligatoriske_aktiviteter,
            merknader,
            fortrinnsrett,
            updated_at,
            processed_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            NOW(),
            NOW()
        )
        ON CONFLICT (emnekode)
        DO UPDATE SET
            navn = EXCLUDED.navn,
            studiepoeng = EXCLUDED.studiepoeng,
            semester = EXCLUDED.semester,
            fakultet = EXCLUDED.fakultet,
            underviser = EXCLUDED.underviser,
            språk = EXCLUDED.språk,
            antall_plasser = EXCLUDED.antall_plasser,
            dette_lærer_du = EXCLUDED.dette_lærer_du,
            forkunnskaper = EXCLUDED.forkunnskaper,
            læringsaktiviteter = EXCLUDED.læringsaktiviteter,
            vurderingsordning = EXCLUDED.vurderingsordning,
            obligatoriske_aktiviteter = EXCLUDED.obligatoriske_aktiviteter,
            merknader = EXCLUDED.merknader,
            fortrinnsrett = EXCLUDED.fortrinnsrett,
            updated_at = NOW(),
            processed_at = NOW();
    """

    values = (
        data.get("emnekode"),
        data.get("navn"),
        data.get("studiepoeng"),
        data.get("semester"),
        data.get("fakultet"),
        data.get("underviser"),
        data.get("språk"),
        data.get("antall_plasser"),
        data.get("dette_lærer_du"),
        data.get("forkunnskaper"),
        data.get("læringsaktiviteter"),
        data.get("vurderingsordning"),
        data.get("obligatoriske_aktiviteter"),
        data.get("merknader"),
        data.get("fortrinnsrett"),
    )

    with conn.cursor() as cur:
        cur.execute(sql, values)


def process_file(filepath: str) -> dict:

    data = parse_file(filepath)

    meaningful = sum(
        1 for v in data.values()
        if isinstance(v, str) and len(v) > 20
    )

    if meaningful < 3:
        return {"status": "skipped"}

    code = data["emnekode"]

    improved = improve_with_openai(data)

    improved["emnekode"] = code

    improved["studiepoeng"] = normalize_float(improved.get("studiepoeng"))
    improved["antall_plasser"] = normalize_integer(improved.get("antall_plasser"))
    improved["semester"] = normalize_semester(improved.get("semester"))

    return {"status": "ok", "data": improved}


def format_eta(seconds):

    m, s = divmod(int(seconds), 60)

    return f"{m}m {s}s"


def main():

    files = [
        os.path.join(SUBJECT_FOLDER, f)
        for f in os.listdir(SUBJECT_FOLDER)
        if f.endswith(".txt")
    ]

    total = len(files)

    processed = skipped = failed = 0

    start_time = time.time()

    print(f"Starter prosessering av {total} emner")

    with psycopg.connect(DATABASE_URL) as conn:

        pending = []

        for f in files:

            code = os.path.splitext(os.path.basename(f))[0]

            if not is_done(conn, code):
                pending.append(f)
            else:
                skipped += 1

        print(f"Gjenstår: {len(pending)} | Hopper over: {skipped}")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:

            futures = {
                pool.submit(process_file, f): f
                for f in pending
            }

            for idx, future in enumerate(as_completed(futures), 1):

                filename = futures[future]

                try:

                    result = future.result()

                    if result["status"] == "skipped":
                        skipped += 1
                        continue

                    update_emne(conn, result["data"])
                    conn.commit()

                    processed += 1

                except Exception as e:

                    failed += 1
                    print(f"[ERROR] {filename}: {e}")

                elapsed = time.time() - start_time
                avg = elapsed / max(1, idx)
                eta = avg * (len(pending) - idx)

                print(
                    f"[{idx}/{len(pending)}] "
                    f"ok={processed} skip={skipped} fail={failed} "
                    f"ETA {format_eta(eta)}"
                )

    print(
        f"Ferdig på {format_eta(time.time() - start_time)} | "
        f"ok={processed} skip={skipped} fail={failed}"
    )


if __name__ == "__main__":
    main()
