import { NextRequest, NextResponse } from "next/server";

interface GradeData {
  grade: string;
  count: number;
  percentage: number;
}

interface GradeStats {
  grades: GradeData[];
  totalStudents: number;
  averageGrade: number;
  failRate: number;
  year: string;
}

function parseCSVData(csvText: string, year: string): GradeStats {
  const lines = csvText.trim().split('\n');

  if (lines.length < 2) {
    return createEmptyStats(year);
  }

  const gradeMap: { [key: string]: number } = {
    A: 0,
    B: 0,
    C: 0,
    D: 0,
    E: 0,
    F: 0,
  };

  let totalStudents = 0;
  let failedStudents = 0;

  // Skip header row and process data rows
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Split by semicolon or comma (CSV can use either)
    const cells = line.split(/[;,]/).map(cell => cell.trim().replace(/"/g, ''));

    // Look for grade column (Karakter) and count column (Antall studenter)
    // The format varies, but typically: Institusjonskode, Emnekode, Årstall, Karakter, Antall
    const gradeIndex = cells.findIndex(c => ['A', 'B', 'C', 'D', 'E', 'F'].includes(c));

    if (gradeIndex !== -1) {
      const grade = cells[gradeIndex];
      const countIndex = gradeIndex + 1;
      const count = countIndex < cells.length ? parseInt(cells[countIndex]) : 0;

      if (gradeMap.hasOwnProperty(grade) && !isNaN(count)) {
        gradeMap[grade] += count;
        totalStudents += count;
        if (grade === 'F') {
          failedStudents += count;
        }
      }
    }
  }

  if (totalStudents === 0) {
    return createEmptyStats(year);
  }

  // Calculate average grade
  const gradeValues = { A: 5, B: 4, C: 3, D: 2, E: 1, F: 0 };
  let totalGradePoints = 0;
  let studentsWithGrade = 0;

  Object.entries(gradeMap).forEach(([grade, count]) => {
    if (grade !== 'F' && count > 0) {
      totalGradePoints += gradeValues[grade as keyof typeof gradeValues] * count;
      studentsWithGrade += count;
    }
  });

  const averageGrade = studentsWithGrade > 0 ? totalGradePoints / studentsWithGrade : 0;
  const failRate = totalStudents > 0 ? (failedStudents / totalStudents) * 100 : 0;

  const grades: GradeData[] = Object.entries(gradeMap).map(([grade, count]) => ({
    grade,
    count,
    percentage: totalStudents > 0 ? (count / totalStudents) * 100 : 0,
  }));

  return {
    grades,
    totalStudents,
    averageGrade,
    failRate,
    year,
  };
}

function createEmptyStats(year: string): GradeStats {
  return {
    grades: [],
    totalStudents: 0,
    averageGrade: 0,
    failRate: 0,
    year,
  };
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const emnekode = searchParams.get('emnekode');
  const year = searchParams.get('year');

  if (!emnekode || !year) {
    return NextResponse.json(
      { error: 'Missing required parameters: emnekode and year' },
      { status: 400 }
    );
  }

  try {
    // DBH API endpoint for CSV data
    const apiUrl = "https://dbh-data.dataporten-api.no/Tabeller/hentCSVTabellData";

    // Query payload for table 308 (grade statistics)
    const queryPayload = {
      tabell_id: 308,
      api_versjon: 1,
      statuslinje: "J",
      kodetekst: "J",
      desimal_separator: ".",
      groupBy: ["Institusjonskode", "Emnekode", "Årstall", "Karakter"],
      sortBy: ["Institusjonskode", "Emnekode"],
      filter: [
        {
          variabel: "Institusjonskode",
          selection: {
            filter: "item",
            values: ["1173"],
            exclude: [""]
          }
        },
        {
          variabel: "Emnekode",
          selection: {
            filter: "item",
            values: [emnekode],
            exclude: [""]
          }
        },
        {
          variabel: "Årstall",
          selection: {
            filter: "item",
            values: [year],
            exclude: [""]
          }
        }
      ]
    };

    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(queryPayload),
    });

    if (!response.ok) {
      console.error("DBH API error:", response.status, response.statusText);
      return NextResponse.json(
        { error: 'Failed to fetch data from DBH API', stats: createEmptyStats(year) },
        { status: response.status }
      );
    }

    const csvData = await response.text();
    console.log("DBH CSV response received for", emnekode, year);

    const stats = parseCSVData(csvData, year);

    return NextResponse.json({ success: true, stats });
  } catch (error: any) {
    console.error("Error fetching grade statistics:", error);
    return NextResponse.json(
      { error: error.message, stats: createEmptyStats(year) },
      { status: 500 }
    );
  }
}
