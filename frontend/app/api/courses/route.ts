import { NextResponse } from "next/server";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl:
    process.env.NODE_ENV === "production"
      ? { rejectUnauthorized: false }
      : false,
});

export async function GET() {
  try {
    const result = await pool.query(`
      SELECT
        emnekode,
        navn,
        studiepoeng,
        semester,
        fakultet,
        underviser
      FROM emner
      ORDER BY emnekode ASC
    `);

    return NextResponse.json({
      success: true,
      data: result.rows,
    });
  } catch (err: any) {
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
