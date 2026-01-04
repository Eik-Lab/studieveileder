import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const emnekode = searchParams.get("emnekode");
  const year = searchParams.get("year");

  if (!emnekode || !year) {
    return NextResponse.json(
      { error: "Missing emnekode or year" },
      { status: 400 }
    );
  }

  const { data, error } = await supabase
    .from("eksamensresultater")
    .select(`
      ar,
      prosent_a,
      prosent_b,
      prosent_c,
      prosent_d,
      prosent_e,
      prosent_f
    `)
    .eq("emnekode", emnekode)
    .eq("ar", Number(year))
    .single();

  if (error || !data) {
    return NextResponse.json(
      { error: "No data found" },
      { status: 404 }
    );
  }

  return NextResponse.json(data);
}
