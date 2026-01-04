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
  averageGrade: number;
  failRate: number;
  year: number;
}

interface GradeStatisticsProps {
  emnekode: string;
}

const GRADE_VALUES: Record<string, number> = {
  A: 5,
  B: 4,
  C: 3,
  D: 2,
  E: 1,
  F: 0,
};

const COLORS: Record<string, string> = {
  A: "#10b981",
  B: "#34d399",
  C: "#fbbf24",
  D: "#fb923c",
  E: "#f87171",
  F: "#dc2626",
};

export default function GradeStatistics({ emnekode }: GradeStatisticsProps) {
  const [stats, setStats] = useState<GradeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(2023);

  const currentYear = new Date().getFullYear();
  const availableYears = Array.from({ length: 8 }, (_, i) => currentYear - 1 - i);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);

      const res = await apiClient.get<{
        ar: number;
        prosent_a: number;
        prosent_b: number;
        prosent_c: number;
        prosent_d: number;
        prosent_e: number;
        prosent_f: number;
      }>(
        `/api/grades?emnekode=${encodeURIComponent(emnekode)}&year=${selectedYear}`,
        { cache: "no-store" }
      );

      const prosent = {
        A: res.prosent_a ?? 0,
        B: res.prosent_b ?? 0,
        C: res.prosent_c ?? 0,
        D: res.prosent_d ?? 0,
        E: res.prosent_e ?? 0,
        F: res.prosent_f ?? 0,
      };

      const grades: GradeData[] = Object.entries(prosent).map(
        ([grade, percentage]) => ({
          grade,
          percentage,
        })
      );

      const passed = grades.filter((g) => g.grade !== "F");
      const sumPassed = passed.reduce((s, g) => s + g.percentage, 0);

      const average =
        sumPassed > 0
          ? passed.reduce(
              (s, g) => s + GRADE_VALUES[g.grade] * g.percentage,
              0
            ) / sumPassed
          : 0;

      setStats({
        grades,
        averageGrade: average,
        failRate: prosent.F,
        year: res.ar,
      });

      setLoading(false);
    };

    fetchStats();
  }, [emnekode, selectedYear]);

  if (loading || !stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Karakterstatistikk</CardTitle>
        </CardHeader>
        <CardContent className="py-12 text-center text-muted-foreground">
          Laster karakterstatistikk…
        </CardContent>
      </Card>
    );
  }

  const averageLetter =
    ["F", "E", "D", "C", "B", "A"][Math.round(stats.averageGrade)] ?? "–";

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
        <div className="grid grid-cols-2 gap-3">
          <Summary
            icon={<Award size={16} />}
            label="Gjennomsnitt"
            value={averageLetter}
          />
          <Summary
            icon={<TrendingUp size={16} />}
            label="Stryk"
            value={`${stats.failRate.toFixed(1)}%`}
          />
        </div>

        <div className="h-80">
          <ResponsiveContainer>
            <BarChart data={stats.grades}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="grade" />
              <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
              <Bar dataKey="percentage">
                {stats.grades.map((g) => (
                  <Cell key={g.grade} fill={COLORS[g.grade]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <p className="text-xs text-center text-muted-foreground">
          Kilde: Intern database ({stats.year})
        </p>
      </CardContent>
    </Card>
  );
}

const Summary = ({ icon, label, value }: any) => (
  <Card>
    <CardContent className="p-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
        {icon}
        {label}
      </div>
      <div className="text-xl font-bold">{value}</div>
    </CardContent>
  </Card>
);
