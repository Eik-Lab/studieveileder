import os
import re
import unicodedata
import pandas as pd
from difflib import SequenceMatcher
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRADES_DIR = os.path.join(BASE_DIR, "grades")

EMNER_TABLE = "emner"
RESULT_TABLE = "eksamensresultater"

YEAR_REGEX = re.compile(r"(\d{4})")
MATCH_THRESHOLD = 0.85


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"\(.*?\)", "", text)
    text = text.split(":")[0]
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def extract_year(filename: str) -> int:
    m = YEAR_REGEX.search(filename)
    if not m:
        raise ValueError(f"Could not extract year from filename: {filename}")
    return int(m.group(1))


def fetch_emner():

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT emnekode, navn FROM emner")
        rows = cur.fetchall()

    return [
        {
            "emnekode": r["emnekode"],
            "navn": r["navn"],
            "norm": normalize(r["navn"]),
        }
        for r in rows
    ]


def parse_excel(path: str):

    df = pd.read_excel(path)

    df = df.rename(columns={
        df.columns[0]: "emnenavn",
        df.columns[1]: "A",
        df.columns[2]: "B",
        df.columns[3]: "C",
        df.columns[4]: "D",
        df.columns[5]: "E",
        df.columns[6]: "F",
        df.columns[7]: "bestatt",
        df.columns[8]: "ikke_bestatt",
    })

    rows = []

    for _, r in df.iterrows():

        if pd.isna(r["emnenavn"]):
            continue

        rows.append({
            "raw_name": str(r["emnenavn"]),
            "norm": normalize(str(r["emnenavn"])),
            "A": r["A"],
            "B": r["B"],
            "C": r["C"],
            "D": r["D"],
            "E": r["E"],
            "F": r["F"],
            "bestatt": r["bestatt"],
            "ikke_bestatt": r["ikke_bestatt"],
        })

    return rows


def match_emne(emne, excel_rows):

    best = None
    best_score = 0.0

    for r in excel_rows:

        score = similarity(emne["norm"], r["norm"])

        if score > best_score:
            best_score = score
            best = r

    if best_score >= MATCH_THRESHOLD:
        return best, best_score

    return None, best_score


def dedupe(rows):

    unique = {}

    for r in rows:
        key = (r["emnekode"], r["ar"])

        if key not in unique:
            unique[key] = r

    return list(unique.values())


def insert_rows(rows):

    if not rows:
        return

    cols = rows[0].keys()

    columns = ",".join(cols)
    placeholders = ",".join(["%s"] * len(cols))
    updates = ",".join(
        [f"{c}=EXCLUDED.{c}" for c in cols if c not in ("emnekode", "ar")]
    )

    query = f"""
    INSERT INTO {RESULT_TABLE} ({columns})
    VALUES ({placeholders})
    ON CONFLICT (emnekode, ar)
    DO UPDATE SET {updates}
    """

    values = [
        tuple(r[c] for c in cols)
        for r in rows
    ]

    with get_conn() as conn, conn.cursor() as cur:
        cur.executemany(query, values)
        conn.commit()


def main():

    emner = fetch_emner()
    total_inserted = 0

    for filename in sorted(os.listdir(GRADES_DIR)):

        if not filename.endswith(".xlsx"):
            continue

        year = extract_year(filename)
        path = os.path.join(GRADES_DIR, filename)

        print(f"Processing {filename} ({year})")

        excel_rows = parse_excel(path)
        rows_to_insert = []

        for emne in emner:

            match, score = match_emne(emne, excel_rows)

            if not match:
                continue

            rows_to_insert.append({
                "emnekode": emne["emnekode"],
                "emnenavn": emne["navn"],
                "ar": year,
                "prosent_a": match["A"],
                "prosent_b": match["B"],
                "prosent_c": match["C"],
                "prosent_d": match["D"],
                "prosent_e": match["E"],
                "prosent_f": match["F"],
                "prosent_bestatt": match["bestatt"],
                "prosent_ikke_bestatt": match["ikke_bestatt"],
            })

        rows_to_insert = dedupe(rows_to_insert)

        insert_rows(rows_to_insert)

        print(f"Inserted {len(rows_to_insert)} rows")

        total_inserted += len(rows_to_insert)

    print(f"Done. Total rows inserted: {total_inserted}")


if __name__ == "__main__":
    main()
