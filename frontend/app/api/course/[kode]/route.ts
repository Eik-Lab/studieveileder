import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ kode: string }> }
) {
  const { kode } = await params;

  const { data, error } = await supabase
    .from("emner")
    .select(`
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
    `)
    .eq("emnekode", kode)
    .single();

  if (error || !data) {
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
    data,
  });
}
