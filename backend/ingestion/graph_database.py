import os
import asyncio
import json
from typing import List, Dict

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase
from openai import OpenAI


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([DATABASE_URL, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY]):
    raise ValueError("Missing environment variables")

openai_client = OpenAI(api_key=OPENAI_API_KEY)


DOMAINS = [
    "Utdanning",
    "Opptak",
    "Vurdering",
    "Regelverk",
    "Forskning",
    "Studentliv",
    "Sosialt",
    "Karriere",
    "Utveksling",
    "Støtte"
]


class PostgresLoader:

    def __init__(self, url: str):
        self.url = url

    def connect(self):
        return psycopg.connect(self.url, row_factory=dict_row)

    def fetch_study_data(self):

        q = """
        SELECT
            s.studie_id,
            s.navn AS studie_navn,
            s.type,

            sp.spesialisering_id,
            sp.navn AS spes_navn,

            e.id AS emne_id,
            e.emnekode,
            e.navn AS emne_navn,
            e.studiepoeng,
            e.semester,
            e.språk,
            e.dette_lærer_du,
            e.forkunnskaper,
            e.læringsaktiviteter,
            e.vurderingsordning,

            sf.studieaar,
            sf.semester AS sf_semester,
            sf.obligatorisk

        FROM studiefag sf
        JOIN studier s ON sf.studie_id = s.studie_id
        JOIN spesialiseringer sp ON sf.spesialisering_id = sp.spesialisering_id
        JOIN emner e ON sf.emne_id = e.id
        ORDER BY s.navn, sp.navn, e.emnekode
        """

        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(q)
                return cur.fetchall()

    def fetch_documents(self):

        q = """
        SELECT
            id,
            url,
            title,
            text,
            embedding
        FROM embeddings
        WHERE text IS NOT NULL
        """

        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(q)
                return cur.fetchall()


class DomainClassifier:

    async def classify(self, text: str) -> List[str]:

        prompt = f"""
Du klassifiserer tekster relatert til universitetsstudier.

Kategorier:

Utdanning: emner, grader, studieplan, læring
Opptak: søknad, krav, frister, poenggrenser
Vurdering: eksamen, sensur, klage, kont
Regelverk: regler, progresjon, studierett
Forskning: prosjekter, publikasjoner, PhD, lab
Studentliv: bolig, campus, aktiviteter
Sosialt: arrangementer, foreninger, frivillighet
Karriere: jobb, praksis, CV, alumni
Utveksling: Erasmus, utlandet, forhåndsgodkjenning
Støtte: tilrettelegging, helse, rådgivning, NAV

Returner kun en JSON-liste med eksakte kategorinavn.

Tekst:
{text[:4000]}
"""

        r = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        try:
            data = json.loads(r.choices[0].message.content)
            return [d for d in data if d in DOMAINS]
        except:
            return ["Utdanning"]


class Neo4jClient:

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    async def close(self):
        await self.driver.close()

    async def run(self, query: str, params: Dict = None):

        async with self.driver.session() as session:
            await session.run(query, params or {})


class KnowledgeGraphBuilder:

    def __init__(self):

        self.pg = PostgresLoader(DATABASE_URL)
        self.neo = Neo4jClient()
        self.classifier = DomainClassifier()

    async def close(self):
        await self.neo.close()

    async def setup_domains(self):

        for d in DOMAINS:

            q = """
            MERGE (:Domain {name:$name})
            """

            await self.neo.run(q, {"name": d})

    async def load_structured(self):

        rows = self.pg.fetch_study_data()

        for r in rows:

            await self._insert_structured(r)

    async def _insert_structured(self, r: Dict):

        q = """
        MERGE (s:Study {id:$sid})
        SET s.name=$sname, s.type=$stype

        MERGE (sp:Specialization {id:$spid})
        SET sp.name=$spname

        MERGE (c:Course {id:$cid})
        SET
            c.code=$code,
            c.name=$cname,
            c.credits=$credits,
            c.language=$lang

        MERGE (s)-[:HAS_SPECIALIZATION]->(sp)

        MERGE (sp)-[:INCLUDES]->(c)

        MERGE (s)-[r:HAS_COURSE]->(c)
        SET
            r.year=$year,
            r.semester=$semester,
            r.mandatory=$mandatory
        """

        await self.neo.run(q, {
            "sid": r["studie_id"],
            "sname": r["studie_navn"],
            "stype": r["type"],

            "spid": r["spesialisering_id"],
            "spname": r["spes_navn"],

            "cid": r["emne_id"],
            "code": r["emnekode"],
            "cname": r["emne_navn"],
            "credits": r["studiepoeng"],
            "lang": r["språk"],

            "year": r["studieaar"],
            "semester": r["sf_semester"],
            "mandatory": r["obligatorisk"]
        })

        await self._assign_course_domain(r["emne_id"])

    async def _assign_course_domain(self, course_id: int):

        q = """
        MATCH (c:Course {id:$id})
        MATCH (d:Domain {name:"Utdanning"})
        MERGE (c)-[:BELONGS_TO]->(d)
        """

        await self.neo.run(q, {"id": course_id})

    async def load_documents(self):

        docs = self.pg.fetch_documents()

        for d in docs:

            await self._insert_document(d)

    async def _insert_document(self, d: Dict):

        domains = await self.classifier.classify(d["text"])

        q = """
        MERGE (doc:Document {id:$id})
        SET
            doc.url=$url,
            doc.title=$title,
            doc.text=$text
        """

        await self.neo.run(q, {
            "id": d["id"],
            "url": d["url"],
            "title": d["title"],
            "text": d["text"]
        })

        for dom in domains:

            await self._link_domain(d["id"], dom)

        await self._link_to_courses(d)

    async def _link_domain(self, doc_id: int, domain: str):

        q = """
        MATCH (doc:Document {id:$id})
        MATCH (d:Domain {name:$domain})
        MERGE (doc)-[:BELONGS_TO]->(d)
        """

        await self.neo.run(q, {
            "id": doc_id,
            "domain": domain
        })

    async def _link_to_courses(self, doc: Dict):

        text = doc["text"].lower()

        q = """
        MATCH (c:Course)
        WHERE ANY(t IN $tokens WHERE
            toLower(c.code) CONTAINS t
            OR toLower(c.name) CONTAINS t
        )
        MERGE (doc:Document {id:$doc_id})
        MERGE (doc)-[:MENTIONS]->(c)
        """

        tokens = self._extract_tokens(text)

        if not tokens:
            return

        await self.neo.run(q, {
            "tokens": tokens,
            "doc_id": doc["id"]
        })

    def _extract_tokens(self, text: str) -> List[str]:

        tokens = set()

        for w in text.split():
            if len(w) > 4:
                tokens.add(w.strip(".,:;()"))

        return list(tokens)[:200]


async def main():

    builder = KnowledgeGraphBuilder()

    try:

        await builder.setup_domains()

        await builder.load_structured()

        await builder.load_documents()

    finally:

        await builder.close()


if __name__ == "__main__":
    asyncio.run(main())
