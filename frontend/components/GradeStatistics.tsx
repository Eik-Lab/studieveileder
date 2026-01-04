"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { TrendingUp, Award } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";

interface GradeData {
  grade: string;
  percentage: number;
}

interface GradeStats {
  grades: GradeData[];
  year: number;
  hasLetterGrades: boolean;
  passRate: number;
  failRate: number;
}

interface GradeStatisticsProps {
  emnekode: string;
}

const COLORS: Record<string, string> = {
  A: "#10b981",
  B: "#34d399",
  C: "#fbbf24",
  D: "#fb923c",
  E: "#f87171",
  F: "#dc2626",
  Bestått: "#10b981",
  "Ikke bestått": "#dc2626",
};

export default function GradeStatistics({ emnekode }: GradeStatisticsProps) {
  const [stats, setStats] = useState<GradeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [noRow, setNoRow] = useState(false);
  const [selectedYear, setSelectedYear] = useState(2024);

  const currentYear = new Date().getFullYear();
  const availableYears = Array.from({ length: 8 }, (_, i) => currentYear - 1 - i);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const fetchStats = async () => {
      setLoading(true);
      setNoRow(false);
      setStats(null);

      timeoutId = setTimeout(() => {
        setLoading(false);
        setNoRow(true);
      }, 2000);

      try {
        const res = await apiClient.get<{
          success: boolean;
          data: {
            ar: number;
            prosent_a: number;
            prosent_b: number;
            prosent_c: number;
            prosent_d: number;
            prosent_e: number;
            prosent_f: number;
            prosent_bestatt: number;
            prosent_ikke_bestatt: number;
          } | null;
        }>(
          `/api/grades?emnekode=${encodeURIComponent(emnekode)}&year=${selectedYear}`,
          { cache: "no-store" }
        );

        clearTimeout(timeoutId);

        if (!res.success || !res.data) {
          setNoRow(true);
          setLoading(false);
          return;
        }

        const letterGrades: GradeData[] = [
          { grade: "A", percentage: res.data.prosent_a ?? 0 },
          { grade: "B", percentage: res.data.prosent_b ?? 0 },
          { grade: "C", percentage: res.data.prosent_c ?? 0 },
          { grade: "D", percentage: res.data.prosent_d ?? 0 },
          { grade: "E", percentage: res.data.prosent_e ?? 0 },
          { grade: "F", percentage: res.data.prosent_f ?? 0 },
        ];

        const totalLetters = letterGrades.reduce(
          (s, g) => s + g.percentage,
          0
        );

        const hasLetterGrades = totalLetters > 0;

        const grades = hasLetterGrades
          ? letterGrades
          : [
              {
                grade: "Bestått",
                percentage: res.data.prosent_bestatt ?? 0,
              },
              {
                grade: "Ikke bestått",
                percentage: res.data.prosent_ikke_bestatt ?? 0,
              },
            ];

        setStats({
          grades,
          year: res.data.ar,
          hasLetterGrades,
          passRate: res.data.prosent_bestatt ?? 0,
          failRate: res.data.prosent_ikke_bestatt ?? 0,
        });

        setLoading(false);
      } catch {
        clearTimeout(timeoutId);
        setLoading(false);
        setNoRow(true);
      }
    };

    fetchStats();
    return () => clearTimeout(timeoutId);
  }, [emnekode, selectedYear]);

  const maxValue = stats
    ? Math.max(...stats.grades.map((g) => g.percentage))
    : 0;

  const yMax =
    maxValue <= 10 ? 10 :
    maxValue <= 25 ? 30 :
    maxValue <= 40 ? 50 :
    maxValue <= 50 ? 60 :
    100;

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <CardTitle>Karakterstatistikk</CardTitle>
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(Number(e.target.value))}
          className="border rounded px-2 py-1 text-sm"
        >
          {availableYears.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </CardHeader>

      <CardContent className="space-y-6">
        {loading && (
          <div className="py-12 text-center text-muted-foreground">
            Laster karakterstatistikk…
          </div>
        )}

        {!loading && noRow && (
          <div className="py-12 text-center text-muted-foreground">
            Ingen karakterdata tilgjengelig for valgt år.
          </div>
        )}

        {!loading && stats && (
          <>
            {!stats.hasLetterGrades && (
              <p className="text-sm text-center text-muted-foreground">
                Dette emnet vurderes som <strong>bestått / ikke bestått</strong>.
              </p>
            )}

            <div className="h-80">
              <ResponsiveContainer>
                <BarChart data={stats.grades}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="grade" />
                  <YAxis
                    domain={[0, yMax]}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
                  <Bar dataKey="percentage">
                    {stats.grades.map((g) => (
                      <Cell
                        key={g.grade}
                        fill={COLORS[g.grade] ?? "#8884d8"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}

        <p className="text-xs text-center text-muted-foreground">
          Kilde: csv eksportert fra dhb.hkdir.no, lagret i intern database
          {stats ? ` (${stats.year})` : ""}
        </p>
      </CardContent>
    </Card>
  );
}
