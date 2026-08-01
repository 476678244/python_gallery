import { NextRequest, NextResponse } from "next/server";
const BACKEND = "http://localhost:8000";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  let body: unknown;
  try {
    body = await request.json();
  } catch (e) {
    return NextResponse.json(
      {
        detail:
          `[skills toggle] Invalid JSON body (Fail Fast)\n` +
          `  id: ${id}\n` +
          `  Error: ${e instanceof Error ? e.message : String(e)}`,
      },
      { status: 400 }
    );
  }
  const res = await fetch(`${BACKEND}/skills/${id}/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
