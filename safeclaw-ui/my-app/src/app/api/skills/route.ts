import { NextRequest, NextResponse } from "next/server";
const BACKEND = "http://localhost:8000";

export async function GET() {
  const res = await fetch(`${BACKEND}/skills`);
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const res = await fetch(`${BACKEND}/skills`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
