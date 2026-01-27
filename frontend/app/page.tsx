import Header from "@/components/Header";
import Footer from "@/components/Footer";
import ServiceCard from "@/components/ServiceCard";
import { Search, MessageCircle, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import Image from "next/image";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#F7F6F2]">

      <main className="flex-1">

        {/* ================= HERO ================= */}
        <section className="relative overflow-hidden bg-[#0D3B34] text-white">
          <Header />

          {/* Soft gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#025C4F] via-[#0D3B34] to-[#008571] opacity-95" />

          {/* Content */}
          <div className="relative container mx-auto px-6 py-28 lg:py-36">

            <div className="max-w-3xl mx-auto text-center">

              {/* Heading */}
              <h1 className="text-4xl md:text-5xl xl:text-6xl font-bold leading-tight mb-6">

                Velkommen til{" "}
                <span className="text-[#5BBEAF]">
                  Eik Labs
                </span>{" "}
                digitale studieveileder

              </h1>

              {/* Subtext */}
              <p className="text-lg md:text-xl text-[#DBF8F4] opacity-90 mb-12 max-w-2xl mx-auto">

                Få hjelp til studierelaterte spørsmål, emnesøk og kontaktinformasjon –
                raskt, presist og tilgjengelig hele døgnet.

              </p>

              {/* Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">

                {/* Primary */}
                <Button
                  asChild
                  size="lg"
                  className="
                    bg-[#5BBEAF]
                    text-[#0D3B34]
                    hover:bg-[#4AA89A]
                    shadow-lg
                    shadow-[#5BBEAF]/20
                  "
                >
                  <Link href="#tjenester">
                    Utforsk tjenestene
                  </Link>
                </Button>

                {/* Secondary */}
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="
                    border-[#DBF8F4]
                    text-[#DBF8F4]
                    hover:bg-white/10
                  "
                >
                  <Link href="/academic_advisor">
                    Start chat
                  </Link>
                </Button>

              </div>

            </div>
          </div>
        </section>


        {/* ================= SERVICES ================= */}
        <section
          id="tjenester"
          className="py-24 bg-[#F7F6F2]"
        >
          <div className="container mx-auto px-6">

            <div className="text-center mb-16">

              <h2 className="text-4xl font-bold text-[#1F3F3A] mb-4">
                Våre tjenester
              </h2>

              <p className="text-lg text-[#5C6F6B] max-w-2xl mx-auto">
                Velg den tjenesten som passer best for dine behov
              </p>

            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10 max-w-6xl mx-auto">

              <ServiceCard
                icon={Search}
                title="Emnesøk"
                description="Søk gjennom alle emner ved NMBU. Finn informasjon om innhold, studiepoeng og oppstart."
                link="/search"
                buttonText="Gå til emnesøk"
                iconColor="text-[#3B7C72]"
              />

              <ServiceCard
                icon={MessageCircle}
                title="Digital studieveileder"
                description="Chat med vår AI-veileder for svar på spørsmål om studier, eksamener og studentliv."
                link="/academic_advisor"
                buttonText="Start chat"
                iconColor="text-[#5BA89C]"
                badge="Under utvikling"
              />

              <ServiceCard
                icon={Mail}
                title="Kontakt oss"
                description="Finn kontaktinformasjon til studieveiledere, administrasjon og teknisk support."
                link="/kontakt"
                buttonText="Se kontakter"
                iconColor="text-[#D9B75A]"
              />

            </div>
          </div>
        </section>


        {/* ================= FEEDBACK ================= */}
        <section className="py-24 bg-[#E6E2D6]">

          <div className="container mx-auto px-6">

            <div className="max-w-3xl mx-auto text-center">

              <Badge
                variant="outline"
                className="mb-6 border-[#3B7C72] text-[#3B7C72]"
              >
                Tilbakemeldinger
              </Badge>

              <h2 className="text-3xl font-bold mb-4 text-[#1F3F3A]">
                Hjelp oss å forbedre tjenestene
              </h2>

              <p className="text-lg text-[#5C6F6B] mb-10">
                Vi setter stor pris på innspill, forslag og feilrapporter.
                Tilbakemeldingene brukes direkte i videre utvikling.
              </p>

              <Button
                asChild
                size="lg"
                className="bg-[#3B7C72] hover:bg-[#2F655D] text-white"
              >
                <Link
                  href="https://nettskjema.no/a/580798"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Gi tilbakemelding
                </Link>
              </Button>

            </div>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
