"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Search, ChevronLeft, ChevronRight, BookOpen } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiClient, isTimeoutError } from "@/lib/api-client";

interface Course {
  kode: string;
  navn: string;
  studiepoeng: number;
  semester: string;
  fakultet: string;
  beskrivelse: string;
}

// Felles mapping (samme som detalj-side)
const mapCourseData = (raw: any): Course => ({
  kode: raw.emnekode || "Ukjent",
  navn: raw.navn || "Ukjent",
  studiepoeng: Number(raw.studiepoeng || 0),
  semester: raw.semester || "Ukjent",
  fakultet: raw.fakultet || "Ukjent",
  beskrivelse: raw.dette_lærer_du || raw.beskrivelse || "",
});

const faculties = [
  "Alle",
  "Handelshøyskolen",
  "Fakultet for biovitenskap",
  "Fakultet for miljøvitenskap og naturforvaltning",
  "Fakultet for realfag og teknologi",
  "Fakultet for veterinærmedisin",
  "Fakultet for samfunnsvitenskap",
];

const semesters = ["Alle", "Høst", "Vår", "Hele året"];
const studiepoengOptions = ["Alle", "5", "7.5", "10", "15", "20", "30"];
const sortOptions = [
  { value: "navn", label: "Emnenavn (A-Å)" },
  { value: "kode", label: "Emnekode" },
  { value: "studiepoeng", label: "Studiepoeng" },
];

const ITEMS_PER_PAGE = 20;

export default function CourseSearch() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFaculty, setSelectedFaculty] = useState("Alle");
  const [selectedSemester, setSelectedSemester] = useState("Alle");
  const [selectedStudiepoeng, setSelectedStudiepoeng] = useState("Alle");
  const [sortBy, setSortBy] = useState<"navn" | "kode" | "studiepoeng">("navn");

  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    async function fetchCourses() {
      setLoading(true);
      setError(null);
      try {
        const result = await apiClient.get<{ success: boolean; data: any[] }>(
          "/api/courses",
          { timeout: 45000 } 
        );

        if (result.success && result.data) {
          const mapped = result.data.map(mapCourseData);
          setCourses(mapped);
        } else {
          setError("Ingen data mottatt fra backend");
        }
      } catch (err: any) {
        if (isTimeoutError(err)) {
          setError("Forespørselen tok for lang tid. Prøv igjen senere.");
        } else {
          setError(err.message || "Kunne ikke hente emner fra backend");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchCourses();
  }, []);

  const filteredCourses = courses
    .filter((c) => {
      const q = searchTerm.toLowerCase().trim();
      return (
        c.navn.toLowerCase().includes(q) ||
        c.kode.toLowerCase().includes(q)
      );
    })
    .filter((c) => selectedFaculty === "Alle" || c.fakultet === selectedFaculty)
    .filter((c) => selectedSemester === "Alle" || c.semester === selectedSemester)
    .filter((c) => selectedStudiepoeng === "Alle" || c.studiepoeng === Number(selectedStudiepoeng))
    .sort((a, b) => {
      if (sortBy === "navn") return a.navn.localeCompare(b.navn);
      if (sortBy === "kode") return a.kode.localeCompare(b.kode);
      if (sortBy === "studiepoeng") return a.studiepoeng - b.studiepoeng;
      return 0;
    });

  const totalPages = Math.ceil(filteredCourses.length / ITEMS_PER_PAGE);
  const paginatedCourses = filteredCourses.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const goToDetail = (kode: string) => router.push(`/course/${kode}`);

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8 md:py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Emnesøk</h1>
          <p className="text-muted-foreground">Søk gjennom alle emner ved NMBU</p>
        </div>

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
                <Input
                  type="text"
                  placeholder="Søk etter emner..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Select value={selectedFaculty} onValueChange={setSelectedFaculty}>
                  <SelectTrigger>
                    <SelectValue placeholder="Fakultet" />
                  </SelectTrigger>
                  <SelectContent>
                    {faculties.map((f) => (
                      <SelectItem key={f} value={f}>{f}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={selectedSemester} onValueChange={setSelectedSemester}>
                  <SelectTrigger>
                    <SelectValue placeholder="Semester" />
                  </SelectTrigger>
                  <SelectContent>
                    {semesters.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={selectedStudiepoeng} onValueChange={setSelectedStudiepoeng}>
                  <SelectTrigger>
                    <SelectValue placeholder="Studiepoeng" />
                  </SelectTrigger>
                  <SelectContent>
                    {studiepoengOptions.map((s) => (
                      <SelectItem key={s} value={s}>{s} sp</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={sortBy} onValueChange={(value) => setSortBy(value as "navn" | "kode" | "studiepoeng")}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sorter etter" />
                  </SelectTrigger>
                  <SelectContent>
                    {sortOptions.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">Laster emner...</p>
            </CardContent>
          </Card>
        ) : error ? (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-6">
              <p className="text-red-600">{error}</p>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Viser {paginatedCourses.length} av {filteredCourses.length} emner
              </p>
            </div>
            <div className="grid gap-4">
              {paginatedCourses.map((c) => (
                <Card
                  key={c.kode}
                  onClick={() => goToDetail(c.kode)}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                >
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <CardTitle className="text-xl mb-2">{c.navn}</CardTitle>
                        <div className="flex flex-wrap gap-2">
                          <Badge className="bg-[#006633] hover:bg-[#004d26]">
                            <BookOpen className="mr-1 h-3 w-3" />
                            {c.kode}
                          </Badge>
                          <Badge variant="secondary">{c.studiepoeng} sp</Badge>
                          {c.semester && c.semester !== "Ukjent" && (
                            <Badge variant="outline">{c.semester}</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-2">{c.fakultet}</p>
                    {c.beskrivelse && (
                      <CardDescription className="line-clamp-3">{c.beskrivelse}</CardDescription>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}

        {totalPages > 1 && !loading && !error && (
          <div className="flex justify-center items-center gap-4 mt-8">
            <Button
              variant="outline"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(currentPage - 1)}
            >
              <ChevronLeft className="mr-2 h-4 w-4" /> Forrige
            </Button>
            <span className="text-sm text-muted-foreground">
              Side {currentPage} av {totalPages}
            </span>
            <Button
              variant="outline"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              Neste <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}