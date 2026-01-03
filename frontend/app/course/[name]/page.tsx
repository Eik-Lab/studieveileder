import Header from "@/components/Header";
import Footer from "@/components/Footer";
import GradeStatistics from "@/components/GradeStatistics";
import BackButton from "./BackButton";
import { ChevronLeft, BookOpen, Clock, GraduationCap, Users, Globe, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { apiClient, isTimeoutError } from "@/lib/api-client";

interface Course {
  kode: string;
  navn: string;
  studiepoeng: number;
  fakultet: string;
  underviser: string;
  språk: string;
  dette_lærer_du: string;
  forkunnskaper: string;
  læringsaktiviteter: string;
  vurderingsordning: string;
  obligatoriske_aktiviteter: string;
  fortrinnsrett: string;
  antall_plasser: string;
  merknader: string;
}

// Felles mapping
const mapCourseData = (raw: any): Course => ({
  kode: raw.emnekode || "Ukjent",
  navn: raw.navn || "Ukjent",
  studiepoeng: Number(raw.studiepoeng) || 0,
  fakultet: raw.fakultet || "Ukjent",
  underviser: raw.underviser || "",
  språk: raw.språk || "",
  dette_lærer_du: raw.dette_lærer_du || "",
  forkunnskaper: raw.forkunnskaper || "",
  læringsaktiviteter: raw.læringsaktiviteter || "",
  vurderingsordning: raw.vurderingsordning || "",
  obligatoriske_aktiviteter: raw.obligatoriske_aktiviteter || "",
  fortrinnsrett: raw.fortrinnsrett || "",
  antall_plasser: raw.antall_plasser || "",
  merknader: raw.merknader || "",
});

async function fetchCourse(kode: string): Promise<{ course: Course | null; error: string | null }> {
  try {
    const result = await apiClient.get<{ success: boolean; data: any }>(
      `/api/course/${encodeURIComponent(kode)}`,
      {
        timeout: 5000, 
        cache: "no-store" // Always fetch fresh data
      }
    );

    if (result.success && result.data) {
      return { course: mapCourseData(result.data), error: null };
    }

    return { course: null, error: "Ingen data mottatt fra backend" };
  } catch (err: any) {
    if (isTimeoutError(err)) {
      return { course: null, error: "Forespørselen tok for lang tid. Prøv igjen senere." };
    }
    if (err.message?.includes("404")) {
      return { course: null, error: `Emnet "${kode}" ble ikke funnet i databasen` };
    }
    return { course: null, error: `Kunne ikke koble til backend: ${err.message}` };
  }
}

export default async function CourseDetail({ params }: { params: Promise<{ name: string }> }) {
  const { name: kode } = await params;
  const { course, error } = await fetchCourse(kode);

  if (!course || error) {
    return (
      <div className="min-h-screen flex flex-col bg-white">
        <Header />
        <main className="flex-1 flex items-center justify-center px-4">
          <Card className="max-w-md w-full">
            <CardHeader>
              <CardTitle className="text-center text-2xl">
                {error || "Kunne ikke hente emne"}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <p className="text-muted-foreground">
                Emnekode: <Badge variant="outline" className="font-mono">{kode}</Badge>
              </p>
              <Button asChild className="w-full bg-[#006633] hover:bg-[#004d26]">
                <Link href="/search">
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Tilbake til emnesøk
                </Link>
              </Button>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-white overflow-hidden">
      <Header />
      <div className="flex-1 overflow-hidden flex">
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 py-8 md:py-12 max-w-5xl">
            <BackButton />

            <div className="mb-8">
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">{course.navn}</h1>
              <div className="flex flex-wrap gap-3 text-sm">
                <Badge className="inline-flex items-center gap-1.5 bg-[#006633] hover:bg-[#004d26] text-white">
                  <BookOpen size={16} />
                  {course.kode}
                </Badge>
                <Badge variant="secondary" className="inline-flex items-center gap-1.5">
                  <Clock size={16} />
                  {course.studiepoeng} sp
                </Badge>
                {course.språk && (
                  <Badge variant="secondary" className="inline-flex items-center gap-1.5">
                    <Globe size={16} />
                    {course.språk}
                  </Badge>
                )}
                {course.underviser && (
                  <Badge variant="secondary" className="inline-flex items-center gap-1.5">
                    <Users size={16} />
                    {course.underviser}
                  </Badge>
                )}
              </div>
              {course.fakultet && (
                <p className="mt-4 text-muted-foreground">
                  <GraduationCap className="inline mr-2" size={18} />
                  {course.fakultet}
                </p>
              )}
            </div>

            <div className="space-y-8">
              <GradeStatistics emnekode={course.kode} />

              {course.dette_lærer_du && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-2xl">Dette lærer du</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-gray max-w-none max-h-80 overflow-y-auto">
                      <p className="text-muted-foreground whitespace-pre-line">{course.dette_lærer_du}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {course.forkunnskaper && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-2xl">Forkunnskaper</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="max-h-80 overflow-y-auto">
                      <p className="text-muted-foreground whitespace-pre-line">{course.forkunnskaper}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {course.læringsaktiviteter && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-2xl">Læringsaktiviteter</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="max-h-80 overflow-y-auto">
                      <p className="text-muted-foreground whitespace-pre-line">{course.læringsaktiviteter}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {course.vurderingsordning && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-2xl">Vurderingsordning</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="max-h-80 overflow-y-auto">
                      <p className="text-muted-foreground whitespace-pre-line">{course.vurderingsordning}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {course.obligatoriske_aktiviteter && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-2xl">Obligatoriske aktiviteter</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="max-h-80 overflow-y-auto">
                      <p className="text-muted-foreground whitespace-pre-line">{course.obligatoriske_aktiviteter}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className="grid sm:grid-cols-2 gap-6">
                {course.fortrinnsrett && (
                  <Card className="bg-blue-50 border-blue-200">
                    <CardHeader>
                      <CardTitle className="text-lg">Fortrinnsrett</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm whitespace-pre-line">{course.fortrinnsrett}</p>
                    </CardContent>
                  </Card>
                )}
                {course.antall_plasser && (
                  <Card className="bg-green-50 border-green-200">
                    <CardHeader>
                      <CardTitle className="text-lg">Antall plasser</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm">{course.antall_plasser}</p>
                    </CardContent>
                  </Card>
                )}
              </div>

              {course.merknader && (
                <Card className="lg:hidden bg-yellow-50 border-yellow-200">
                  <CardHeader>
                    <CardTitle className="text-xl">Merknader</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm leading-relaxed whitespace-pre-line">{course.merknader}</p>
                  </CardContent>
                </Card>
              )}
            </div>

            <div className="mt-12 pt-8 border-t border-gray-200 pb-8">
              <Button asChild className="bg-[#006633] hover:bg-[#004d26]">
                <Link href="/search">
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Tilbake til emnesøk
                </Link>
              </Button>
            </div>
          </div>
        </main>

        {course.merknader && (
          <aside className="hidden lg:block w-80 xl:w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="sticky top-0 p-6">
              <Alert className="mb-6 bg-blue-50 border-blue-200">
                <AlertCircle className="h-4 w-4 text-blue-600" />
                <AlertDescription className="space-y-1">
                  <p className="text-xs font-semibold text-blue-900">Midlertidig oversikt</p>
                  <p className="text-xs text-blue-800">
                    Dette er basert på tilgjengelig informasjon. Se offisiell emnebeskrivelse for fullstendig info.
                  </p>
                </AlertDescription>
              </Alert>

              <Card className="bg-yellow-50 border-yellow-200">
                <CardHeader>
                  <CardTitle className="text-lg">Merknader</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-[calc(100vh-250px)] overflow-y-auto pr-2">
                    <p className="text-sm leading-relaxed whitespace-pre-line">{course.merknader}</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </aside>
        )}
      </div>
      <Footer />
    </div>
  );
}