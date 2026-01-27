import os
import re
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SUBJECT_FOLDER = "parsing-python/subject_contents"


SEMESTER_PATTERNS = {
    "August": re.compile(r"\baugust\b|augustblokk", re.I),
    "Juni": re.compile(r"\bjuni\b|juniblokk", re.I),
    "Januar": re.compile(r"\bjanuar\b|januarblokk", re.I),
    "Høst": re.compile(r"\bhøst\b|høstparallell|høstsemester", re.I),
    "Vår": re.compile(r"\bvår\b|vårparallell|vårsemester", re.I),
}


def extract_semester_exact(path: str) -> str | None:
    """
    Finn linjen 'Undervisnings- og vurderingsperiode:'
    Returner KUN første ikke-tomme linje etter
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.rstrip() for l in f.readlines()]

    for i, line in enumerate(lines):
        if line.strip() == "Undervisnings- og vurderingsperiode:":
            for next_line in lines[i + 1:]:
                if next_line.strip():
                    return next_line.strip()
            return None
    return None


def infer_semester(text: str) -> str | None:
    """
    Regex-basert inferens av semester.
    Returnerer én av:
    August, Juni, Januar, Høst, Vår, Hele året
    """
    if not text:
        return None

    t = text.lower()

    has_høst = SEMESTER_PATTERNS["Høst"].search(t)
    has_vår = SEMESTER_PATTERNS["Vår"].search(t)

    # Høst + vår → Hele året
    if has_høst and has_vår:
        return "Hele året"

    # Prioritert blokk-rekkefølge
    for semester in ["August", "Juni", "Januar", "Høst", "Vår"]:
        if SEMESTER_PATTERNS[semester].search(t):
            return semester

    return None


def main():
    files = [f for f in os.listdir(SUBJECT_FOLDER) if f.endswith(".txt")]

    updated = 0
    missing = 0
    no_match = 0
    no_row = 0

    print(f"Setter semester for {len(files)} emner\n")

    for filename in files:
        emnekode = os.path.splitext(filename)[0]
        path = os.path.join(SUBJECT_FOLDER, filename)

        raw = extract_semester_exact(path)

        if raw is None:
            missing += 1
            continue

        semester = infer_semester(raw)

        if semester is None:
            no_match += 1
            print(f"[INGEN TREFF] {emnekode}: '{raw}'")
            continue

        res = (
            supabase
            .table("emner")
            .update({"semester": semester})
            .eq("emnekode", emnekode)
            .execute()
        )

        if res.data:
            updated += 1
            print(f"[OK] {emnekode}: {semester}")
        else:
            no_row += 1
            print(f"[SKIP] {emnekode}: ingen DB-rad")

    print("\nFERDIG")
    print(f"Oppdatert: {updated}")
    print(f"Mangler blokk: {missing}")
    print(f"Ingen regex-treff: {no_match}")
    print(f"Ingen DB-rad: {no_row}")


if __name__ == "__main__":
    main()
