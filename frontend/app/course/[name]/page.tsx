import Header from "@/components/Header";
import Footer from "@/components/Footer";
import GradeStatistics from "@/components/GradeStatistics";
import BackButton from "./BackButton";
import {
  ChevronLeft,
  BookOpen,
  Clock,
  GraduationCap,
  Users,
  Globe,
  AlertCircle,
  Calendar,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { apiClient, isTimeoutError } from "@/lib/api-client";

interface Course {
  kode: string;
  navn: string;
  studiepoeng: number;
  semester: string;
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

const mapCourseData = (raw: any): Course => ({
  kode: raw.emnekode || "Ukjent",
  navn: raw.navn || "Ukjent",
  studiepoeng: Number(raw.studiepoeng) || 0,
  semester: raw.semester || "",
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

async function fetchCourse(
  kode: string
): Promise<{ course: Course | null; error: string | null }> {
  try {
    const result = await apiClient.get<{ success: boolean; data: any }>(
      `/api/course/${encodeURIComponent(kode)}`,
      { timeout: 45000, cache: "no-store" }
    );

    if (result.success && result.data) {
      return { course: mapCourseData(result.data), error: null };
    }

    return { course: null, error: "Ingen data mottatt fra backend" };
  } catch (err: any) {
    if (isTimeoutError(err)) {
      return {
        course: null,
        error: "Forespørselen tok for lang tid. Prøv igjen senere.",
      };
    }
    if (err.message?.includes("404")) {
      return {
        course: null,
        error: `Emnet "${kode}" ble ikke funnet i databasen`,
      };
    }
    return {
      course: null,
      error: `Kunne ikke koble til backend: ${err.message}`,
    };
  }
}

export default async function CourseDetail({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
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
                Emnekode:{" "}
                <Badge variant="outline" className="font-mono">
                  {kode}
                </Badge>
              </p>
              <Button
                asChild
                className="w-full bg-[#006633] hover:bg-[#004d26]"
              >
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
    <div className="min-h-screen flex flex-col bg-white">
      <Header />

      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 py-6 sm:py-8 md:py-12 max-w-5xl">
          <BackButton />

          {/* HEADER */}
          <div className="mb-8">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {course.navn}
            </h1>

            {/* 🔧 RESPONSIV METADATA */}
            <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2 sm:gap-3 text-sm">
              <Badge className="inline-flex items-center gap-1.5 bg-[#006633] text-white w-fit">
                <BookOpen size={14} />
                {course.kode}
              </Badge>

              <Badge
                variant="secondary"
                className="inline-flex items-center gap-1.5 w-fit"
              >
                <Clock size={14} />
                {course.studiepoeng} sp
              </Badge>

              {course.semester && (
                <Badge
                  variant="secondary"
                  className="inline-flex items-center gap-1.5 w-fit"
                >
                  <Calendar size={14} />
                  {course.semester}
                </Badge>
              )}

              {course.språk && (
                <Badge
                  variant="secondary"
                  className="inline-flex items-center gap-1.5 w-fit"
                >
                  <Globe size={14} />
                  {course.språk}
                </Badge>
              )}

              {course.underviser && (
                <Badge
                  variant="secondary"
                  className="inline-flex items-center gap-1.5 w-fit"
                >
                  <Users size={14} />
                  {course.underviser}
                </Badge>
              )}
            </div>

            {course.fakultet && (
              <p className="mt-3 text-sm sm:text-base text-muted-foreground">
                <GraduationCap className="inline mr-2" size={16} />
                {course.fakultet}
              </p>
            )}
          </div>

          {/* CONTENT */}
          <div className="space-y-8">
            <GradeStatistics key={course.kode} emnekode={course.kode} />

            {course.dette_lærer_du && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl sm:text-2xl">
                    Dette lærer du
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground whitespace-pre-line">
                    {course.dette_lærer_du}
                  </p>
                </CardContent>
              </Card>
            )}

            {course.forkunnskaper && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl sm:text-2xl">
                    Forkunnskaper
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground whitespace-pre-line">
                    {course.forkunnskaper}
                  </p>
                </CardContent>
              </Card>
            )}

            {course.læringsaktiviteter && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl sm:text-2xl">
                    Læringsaktiviteter
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground whitespace-pre-line">
                    {course.læringsaktiviteter}
                  </p>
                </CardContent>
              </Card>
            )}

            {course.vurderingsordning && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl sm:text-2xl">
                    Vurderingsordning
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground whitespace-pre-line">
                    {course.vurderingsordning}
                  </p>
                </CardContent>
              </Card>
            )}

            {course.obligatoriske_aktiviteter && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl sm:text-2xl">
                    Obligatoriske aktiviteter
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground whitespace-pre-line">
                    {course.obligatoriske_aktiviteter}
                  </p>
                </CardContent>
              </Card>
            )}

            {course.merknader && (
              <Card className="bg-yellow-50 border-yellow-200">
                <CardHeader>
                  <CardTitle className="text-xl sm:text-2xl flex items-center gap-2">
                    <AlertCircle className="h-5 w-5 text-yellow-700" />
                    Merknader
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed whitespace-pre-line text-gray-800">
                    {course.merknader}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          <div className="mt-12 pt-8 border-t border-gray-200">
            <Button asChild className="bg-[#006633] hover:bg-[#004d26]">
              <Link href="/search">
                <ChevronLeft className="mr-2 h-4 w-4" />
                Tilbake til emnesøk
              </Link>
            </Button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
