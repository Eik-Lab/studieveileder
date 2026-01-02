import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

STUDY_TYPES = {
    "Bachelor": "Bachelor",
    "Master 2 år": "Master 2 år",
    "Master (5-årig)": "Master 5-årig",
    "Doktorgrad (Ph.d.)": "PhD",
    "Profesjonsstudium": "Profesjonsstudium",
    "Årsstudium": "Årsstudium",
    "Ettårig grunnstudium": "Ettårig",
}

IGNORED_HEADERS = {
    "Andre studier",
    "Etter- og videreutdanning",
    "Emner, kurs og videreutdanning",
    "Lærer- og lektorutdanning",
    "Matematikk, natur- og realfag",
    "Teknologi, sivilingeniør og arkitektur",
    "Veterinærmedisin, dyrepleie og helsefag",
    "Økonomi og administrasjon",
    "Annet",
}

def parse_file(path: str):
    current_type = None
    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if line in STUDY_TYPES:
                current_type = STUDY_TYPES[line]
                continue

            if line in IGNORED_HEADERS:
                continue

            if current_type:
                rows.append({
                    "navn": line,
                    "type": current_type
                })

    return rows


def insert_studies(rows):
    for row in rows:
        supabase.table("studier").upsert(
            row,
            on_conflict="navn"
        ).execute()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "studier.txt")

    rows = parse_file(path)
    insert_studies(rows)

    print(f"La inn {len(rows)} studier")


if __name__ == "__main__":
    main()
