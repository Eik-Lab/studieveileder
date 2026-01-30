import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL")


conn = psycopg.connect(DATABASE_URL)
conn.autocommit = True


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


def get_cursor():
    return conn.cursor()


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
                rows.append(
                    (
                        line,
                        current_type,
                    )
                )

    return rows


def insert_studies(rows):
    with get_cursor() as cur:
        for navn, study_type in rows:
            cur.execute(
                """
                INSERT INTO studier (navn, type)
                VALUES (%s, %s)
                ON CONFLICT (navn)
                DO UPDATE SET type = EXCLUDED.type
                """,
                (navn, study_type),
            )


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "studier.txt")

    rows = parse_file(path)

    insert_studies(rows)

    print(f"La inn {len(rows)} studier")


if __name__ == "__main__":
    main()
