from pathlib import Path

REMOVE_LINES = {
    "| NMBU",
    "Biblioteket",
    "Hopp til hovedinnhold",
    "Om NMBU",
    "Om oss",
    "Finn en ansatt",
    "Jobb hos oss",
    "Alumni",
    "Presse",
    "Kontakt oss",
    "Forskning",
    "Innovasjon",
    "Laboratorier og tjenester",
    "Bærekraftige NMBU",
    "Dyresykehuset",
    "For studenter",
    "Studentlivet",
    "Canvas",
    "Studier og emner",
    "Studenttinget",
    "Lag og foreninger",
    "Si fra om avvik",
    "Kvalitet i utdanningen",
    "Telefon",
    "E-post",
    "Adresse",
    "Postboks 5003",
    "1432 Ås",
    "Organisasjonsnummer",
    "969159570",
    "Besøksadresser",
    "Facebook",
    "Instagram",
    "Linkedin",
    "Snapchat",
    "Tilgjengelighetserklæring",
    "Personvernerklæring",
    "Endre cookies",
    ":",
    "67 23 00 00",
}

def clean_file(path: Path):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    cleaned = [l for l in lines if l.strip() not in REMOVE_LINES]
    path.write_text("\n".join(cleaned), encoding="utf-8")

def process_folder(folder: str):
    for path in Path(folder).rglob("*"):
        if path.is_file():
            clean_file(path)

if __name__ == "__main__":
    process_folder("parsing-python/subject_contents")
