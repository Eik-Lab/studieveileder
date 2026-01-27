import scrapy
import re
from urllib.parse import urlparse


class NmbuStudierSpider(scrapy.Spider):

    name = "nmbu_studier"

    allowed_domains = ["nmbu.no"]

    start_urls = [
        "https://www.nmbu.no/studier",
        "https://www.nmbu.no/studenter",
        "https://www.nmbu.no/forskning",
        "https://www.nmbu.no/fakulteter",
        "https://www.nmbu.no/om",

        "https://www.nmbu.no/studenter/eksamen",
        "https://www.nmbu.no/studenter/vurdering",
        "https://www.nmbu.no/studenter/klage",
        "https://www.nmbu.no/studenter/permisjon",
        "https://www.nmbu.no/studenter/tilrettelegging",
        "https://www.nmbu.no/studenter/utveksling",

        "https://www.nmbu.no/studier/opptak",
        "https://www.nmbu.no/studier/soknad",
        "https://www.nmbu.no/studier/krav",
        "https://www.nmbu.no/studier/utveksling",

        "https://www.nmbu.no/om/regler",
        "https://www.nmbu.no/om/forskrifter",
        "https://www.nmbu.no/om/styringsdokumenter",
        "https://www.nmbu.no/om/varsling",
        "https://www.nmbu.no/om/personvern",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "DEPTH_LIMIT": 6,
        "USER_AGENT": "Mozilla/5.0 (compatible; NMBUStudierBot/1.0)",
        "FEED_EXPORT_ENCODING": "utf-8",
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",
    }

    allowed_paths = [
        "/studier",
        "/studenter",
        "/forskning",
        "/fakulteter",
        "/om",
    ]

    blocked_patterns = [
        r"/emner/",
        r"/kurs/",
        r"/nyheter",
        r"/arrangement",
        r"/stilling",
        r"/jobb",
        r"/presse",
    ]

    noise_patterns = [
        "Postboks 5003",
        "Organisasjonsnummer",
        "Telefon :",
        "Telefon:",
        "Tlf.",
    ]


    def clean_text(self, text: str) -> str:

        for n in self.noise_patterns:
            text = text.replace(n, "")

        text = re.sub(r"\s+", " ", text)

        return text.strip()


    def is_blocked(self, path: str) -> bool:

        for pat in self.blocked_patterns:
            if re.search(pat, path):
                return True

        return False


    def parse(self, response):

        title = response.css("title::text").get()

        texts = response.css("main *::text").getall()

        text = " ".join(t.strip() for t in texts if t.strip())

        text = self.clean_text(text)

        if len(text) > 200:

            yield {
                "url": response.url,
                "title": title,
                "text": text,
            }

        links = response.css("a::attr(href)").getall()

        for link in links:

            if not link:
                continue

            full_url = response.urljoin(link)

            clean_url = full_url.split("#")[0].split("?")[0]

            parsed = urlparse(clean_url)

            if "nmbu.no" not in parsed.netloc:
                continue

            if not any(parsed.path.startswith(p) for p in self.allowed_paths):
                continue

            if self.is_blocked(parsed.path):
                continue

            yield response.follow(clean_url, self.parse)
