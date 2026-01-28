"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  AlertCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

const semesters = [
  "Alle",
  "Vår",
  "Høst",
  "August",
  "Juni",
  "Januar",
  "Hele året",
];

const studiepoengOptions = ["Alle", "5", "7.5", "10", "15", "20", "30"];

const sortOptions = [
  { value: "navn", label: "Emnenavn (A–Å)" },
  { value: "kode", label: "Emnekode" },
  { value: "studiepoeng", label: "Studiepoeng" },
  { value: "semester", label: "Semester" },
];

const SEMESTER_ORDER: Record<string, number> = {
  Vår: 1,
  Januar: 2,
  Juni: 3,
  August: 4,
  Høst: 5,
  "Hele året": 6,
  Ukjent: 7,
};

const ITEMS_PER_PAGE = 20;

export default function CourseSearch() {
  const router = useRouter();
  const listRef = useRef<HTMLDivElement>(null);

  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFaculty, setSelectedFaculty] = useState("Alle");
  const [selectedSemester, setSelectedSemester] = useState("Alle");
  const [selectedStudiepoeng, setSelectedStudiepoeng] = useState("Alle");
  const [sortBy, setSortBy] =
    useState<"navn" | "kode" | "studiepoeng" | "semester">("navn");

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
          setCourses(result.data.map(mapCourseData));
        } else {
          setError("Ingen data mottatt fra backend");
        }
      } catch (err: any) {
        if (isTimeoutError(err)) {
          setError("Forespørselen tok for lang tid. Prøv igjen senere.");
        } else {
          setError(err.message || "Kunne ikke hente emner");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchCourses();
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [
    searchTerm,
    selectedFaculty,
    selectedSemester,
    selectedStudiepoeng,
    sortBy,
  ]);

  const filteredCourses = courses
    .filter((c) => {
      const q = searchTerm.toLowerCase().trim();
      return c.navn.toLowerCase().includes(q) || c.kode.toLowerCase().includes(q);
    })
    .filter((c) => selectedFaculty === "Alle" || c.fakultet === selectedFaculty)
    .filter((c) => selectedSemester === "Alle" || c.semester === selectedSemester)
    .filter(
      (c) =>
        selectedStudiepoeng === "Alle" ||
        c.studiepoeng === Number(selectedStudiepoeng)
    )
    .sort((a, b) => {
      if (sortBy === "navn") return a.navn.localeCompare(b.navn);
      if (sortBy === "kode") return a.kode.localeCompare(b.kode);
      if (sortBy === "studiepoeng") return a.studiepoeng - b.studiepoeng;
      if (sortBy === "semester") {
        return (
          (SEMESTER_ORDER[a.semester] ?? 99) -
          (SEMESTER_ORDER[b.semester] ?? 99)
        );
      }
      return 0;
    });

  const totalPages = Math.ceil(filteredCourses.length / ITEMS_PER_PAGE);

  const paginatedCourses = filteredCourses.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const goToDetail = (kode: string) => router.push(`/course/${kode}`);

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F6F2]">
      <Header />

      <main className="flex-1 pt-12 pb-24">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="lg:hidden mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />

            <div>
              <h3 className="font-semibold text-amber-900 mb-1">
                Under utvikling
              </h3>

              <p className="text-sm text-amber-800">
                Kontakt:{" "}
                <a
                  href="mailto:studieveiledning@nmbu.no"
                  className="underline"
                >
                  studieveiledning@nmbu.no
                </a>
              </p>
            </div>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl md:text-4xl text-[#1F3F3A] font-semibold mb-2">
              Emnesøk
            </h1>

            <p className="text-[#5C6F6B]">
              Søk og filtrer emner basert på innhold, semester, studiepoeng og
              fakultet.
            </p>
          </div>

          <Card
            className="
              mb-6
              shadow-2xl
              border
              border-[#D6E6E2]
              bg-[#F7F6F2]
            "
          >
            <CardContent className="pt-6 space-y-4">
              {/* Search */}
              <div className="relative flex items-center">
                <Search
                  className="absolute left-3 text-[#5C6F6B]"
                  size={20}
                />

                <Input
                  placeholder="Søk på emnenavn eller emnekode"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="
                    pl-10
                    h-11
                    bg-white
                    border-[#5BA89C]
                    focus:ring-[#5BA89C]
                  "
                />
              </div>

              <p className="text-xs text-[#5C6F6B]">
                Fritekstsøk i emnenavn og emnekode.
              </p>

              {/* Filters */}
              <div className="grid grid-cols-2 md:grid-cols-[1.6fr_1fr_1fr_1fr] gap-x-6 gap-y-4">
                {/* Faculty */}
                <div className="mb-20 md:mb-0">
                  <Select value={selectedFaculty} onValueChange={setSelectedFaculty}>
                    <SelectTrigger
                      className="
                        h-11
                        bg-white
                        border-[#5BA89C]
                        focus:ring-[#5BA89C]
                      "
                    >
                      <SelectValue placeholder="Fakultet" />
                    </SelectTrigger>

                    <SelectContent className="bg-white border shadow-lg">
                      {faculties.map((f) => (
                        <SelectItem key={f} value={f}>
                          {f}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Semester */}
                <div>
                  <Select value={selectedSemester} onValueChange={setSelectedSemester}>
                    <SelectTrigger
                      className="
                        h-11
                        bg-white
                        border-[#5BA89C]
                        focus:ring-[#5BA89C]
                      "
                    >
                      <SelectValue placeholder="Semester" />
                    </SelectTrigger>

                    <SelectContent className="bg-white border shadow-lg">
                      {semesters.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Studiepoeng */}
                <div>
                  <Select
                    value={selectedStudiepoeng}
                    onValueChange={setSelectedStudiepoeng}
                  >
                    <SelectTrigger
                      className="
                        h-11
                        bg-white
                        border-[#5BA89C]
                        focus:ring-[#5BA89C]
                      "
                    >
                      <SelectValue placeholder="Studiepoeng" />
                    </SelectTrigger>

                    <SelectContent className="bg-white border shadow-lg">
                      {studiepoengOptions.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s} sp
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Sort */}
                <div>
                  <Select
                    value={sortBy}
                    onValueChange={(v) =>
                      setSortBy(
                        v as "navn" | "kode" | "studiepoeng" | "semester"
                      )
                    }
                  >
                    <SelectTrigger
                      className="
                        h-11
                        bg-white
                        border-[#5BA89C]
                        focus:ring-[#5BA89C]
                      "
                    >
                      <SelectValue placeholder="Sorter etter" />
                    </SelectTrigger>

                    <SelectContent className="bg-white border shadow-lg">
                      {sortOptions.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p>
                    Sorter etter
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div ref={listRef} className="grid gap-4">
            {loading && (
              <div className="text-center text-[#5C6F6B] py-12">
                Laster emner...
              </div>
            )}

            {error && (
              <div className="text-center text-red-600 py-12">{error}</div>
            )}

            {!loading &&
              !error &&
              paginatedCourses.map((c) => (
                <Card
                  key={c.kode}
                  onClick={() => goToDetail(c.kode)}
                  className="
                    cursor-pointer
                    hover:shadow-lg
                    transition
                    border
                    border-[#D6E6E2]
                  "
                >
                  <CardHeader>
                    <CardTitle className="text-xl text-[#1F3F3A] mb-2">
                      {c.navn}
                    </CardTitle>

                    <div className="flex flex-wrap gap-2">
                      <Badge className="bg-[#3B7C72]">
                        <BookOpen className="mr-1 h-3 w-3" />
                        {c.kode}
                      </Badge>

                      <Badge variant="secondary">{c.studiepoeng} sp</Badge>

                      {c.semester !== "Ukjent" && (
                        <Badge variant="outline">{c.semester}</Badge>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent>
                    <p className="text-sm text-[#5C6F6B] mb-2">
                      {c.fakultet}
                    </p>

                    {c.beskrivelse && (
                      <CardDescription className="line-clamp-3 text-[#1F3F3A]">
                        {c.beskrivelse}
                      </CardDescription>
                    )}
                  </CardContent>
                </Card>
              ))}

            {!loading &&
              !error &&
              paginatedCourses.length === 0 && (
                <div className="text-center text-[#5C6F6B] py-12">
                  Ingen emner funnet.
                </div>
              )}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-10">
              <Button
                variant="outline"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
                className="border-[#5BA89C]"
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Forrige
              </Button>

              <span className="text-sm text-[#5C6F6B]">
                Side {currentPage} av {totalPages}
              </span>

              <Button
                variant="outline"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
                className="border-[#5BA89C]"
              >
                Neste
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
