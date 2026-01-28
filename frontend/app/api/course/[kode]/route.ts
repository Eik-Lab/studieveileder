import { NextResponse } from "next/server";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === "production"
    ? { rejectUnauthorized: false }
    : false,
});

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ kode: string }> }
) {
  const { kode } = await params;

  try {
    const result = await pool.query(
      `
      SELECT
        emnekode,
        navn,
        studiepoeng,
        semester,
        fakultet,
        underviser,
        språk,
        dette_lærer_du,
        forkunnskaper,
        læringsaktiviteter,
        vurderingsordning,
        obligatoriske_aktiviteter,
        fortrinnsrett,
        antall_plasser,
        merknader
      FROM emner
      WHERE emnekode = $1
      LIMIT 1
      `,
      [kode]
    );

    if (result.rows.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: `Emnet ${kode} ble ikke funnet`,
        },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: result.rows[0],
    });
  } catch (err) {
    console.error("DB error:", err);

    return NextResponse.json(
      {
        success: false,
        error: "Database error",
      },
      { status: 500 }
    );
  }
}
