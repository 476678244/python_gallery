import { NextResponse } from "next/server";

const BACKEND = "http://localhost:8000";

export async function POST() {
  const res = await fetch(`${BACKEND}/memory/cleanup`, { method: "POST" });
  let data: unknown;
  try {
    data = await res.json();
  } catch (e) {
    return NextResponse.json(
      {
        success: false,
        detail:
          `[memory/cleanup] Backend returned non-JSON (Fail Fast)\n` +
          `  Status: ${res.status}\n` +
          `  Error: ${e instanceof Error ? e.message : String(e)}`,
      },
      { status: res.status === 200 ? 502 : res.status }
    );
  }
  return NextResponse.json(data, { status: res.status });
}
