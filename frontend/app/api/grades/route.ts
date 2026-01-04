import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

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

    const { data, error } = await supabase
      .from("eksamensresultater")
      .select(
        `
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
      `
      )
      .eq("emnekode", emnekode)
      .eq("ar", Number(year))
      .maybeSingle();

    if (error) {
      console.error("Supabase error:", error);
      return NextResponse.json(
        { success: false, error: "Databasefeil" },
        { status: 500 }
      );
    }

    if (!data) {
      return NextResponse.json({
        success: true,
        data: null,
        message: "Ingen karakterdata for valgt år",
      });
    }

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
    console.error("Grades API crash:", err);
    return NextResponse.json(
      { success: false, error: "Intern serverfeil" },
      { status: 500 }
    );
  }
}
