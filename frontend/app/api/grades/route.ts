import { NextResponse } from "next/server";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl:
    process.env.NODE_ENV === "production"
      ? { rejectUnauthorized: false }
      : false,
});

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);

    const emnekode = searchParams.get("emnekode");
    const year = searchParams.get("year");

    if (!emnekode || !year) {
      return NextResponse.json(
        { success: false, error: "Mangler emnekode eller år" },
        { status: 400 }
      );
    }

    const result = await pool.query(
      `
      SELECT
        emnekode,
        emnenavn,
        ar,
        prosent_a,
        prosent_b,
        prosent_c,
        prosent_d,
        prosent_e,
        prosent_f,
        prosent_bestatt,
        prosent_ikke_bestatt
      FROM eksamensresultater
      WHERE emnekode = $1
        AND ar = $2
      LIMIT 1
      `,
      [emnekode, Number(year)]
    );

    if (result.rows.length === 0) {
      return NextResponse.json({
        success: true,
        data: null,
        message: "Ingen karakterdata for valgt år",
      });
    }

    const data = result.rows[0];

    return NextResponse.json({
      success: true,
      data: {
        emnekode: data.emnekode,
        emnenavn: data.emnenavn,
        ar: data.ar,
        prosent_a: data.prosent_a,
        prosent_b: data.prosent_b,
        prosent_c: data.prosent_c,
        prosent_d: data.prosent_d,
        prosent_e: data.prosent_e,
        prosent_f: data.prosent_f,
        prosent_bestatt: data.prosent_bestatt,
        prosent_ikke_bestatt: data.prosent_ikke_bestatt,
      },
    });
  } catch (err) {
    console.error("DB error:", err);

    return NextResponse.json(
      { success: false, error: "Intern serverfeil" },
      { status: 500 }
    );
  }
}
