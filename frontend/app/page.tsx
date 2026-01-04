import Header from "@/components/Header";
import Footer from "@/components/Footer";
import ServiceCard from "@/components/ServiceCard";
import { Search, MessageCircle, Mail, Info, Shield, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import Image from "next/image";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="bg-[#E8E0D5] py-12 md:py-16 lg:py-24">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
              <div className="max-w-lg mx-auto lg:mx-0 text-center lg:text-left">
                <h1 className="text-4xl lg:text-5xl font-bold mb-6 text-gray-900 leading-tight">
                  Velkommen til Eik Labs digitale studieveileder
                </h1>
                <p className="text-lg text-muted-foreground mb-8">
                  Få hjelp til dine studierelaterte spørsmål, søk etter emner, eller finn kontaktinformasjon.
                </p>
                <Button asChild size="lg" className="bg-[#006633] hover:bg-[#004d26]">
                  <Link href="#tjenester">Utforsk tjenestene</Link>
                </Button>
              </div>

              <div className="hidden md:flex justify-center lg:justify-end">
                <Image
                  src="/hero.svg"
                  alt="Student ved datamaskin"
                  width={600}
                  height={400}
                  className="w-full h-auto"
                  priority
                />
              </div>
            </div>
          </div>
        </section>

        {/* Services Grid */}
        <section id="tjenester" className="bg-[#F5F5F5] py-20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold mb-4 text-gray-900">Våre tjenester</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Velg den tjenesten som passer best for ditt behov
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
              <ServiceCard
                icon={Search}
                title="Emnesøk"
                description="Søk gjennom alle emner ved NMBU. Finn informasjon om innhold, studiepoeng og oppstart."
                link="/search"
                buttonText="Gå til emnesøk"
                iconColor="text-[#0062BA]"
              />
              <ServiceCard
                icon={MessageCircle}
                title="Digital studieveileder"
                description="Chat med vår AI-veileder for svar på spørsmål om studier, eksamener og studentliv."
                link="/academic_advisor"
                buttonText="Start chat"
                iconColor="text-[#006633]"
                badge="Under utvikling"
              />
              <ServiceCard
                icon={Mail}
                title="Kontakt oss"
                description="Finn kontaktinformasjon til studieveiledere, administrasjon og teknisk support."
                link="/kontakt"
                buttonText="Se kontakter"
                iconColor="text-[#F5A623]"
              />
            </div>
          </div>
        </section>

        {/* Feedback Section */}
        <section className="bg-[#E8E0D5] py-16">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto text-center">
              <Badge variant="outline" className="mb-4">
                Tilbakemeldinger
              </Badge>
              <h2 className="text-3xl font-bold mb-4 text-gray-900">
                Hjelp oss å forbedre tjenestene
              </h2>
              <p className="text-lg text-muted-foreground mb-8">
                Vi setter stor pris på innspill, forslag og feilrapporter.  
                Tilbakemeldingene brukes direkte i videre utvikling.
              </p>
              <Button
                asChild
                size="lg"
                className="bg-[#006633] hover:bg-[#004d26]"
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