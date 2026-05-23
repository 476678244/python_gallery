import { NextRequest, NextResponse } from "next/server";
const BACKEND = "http://localhost:8000";

export async function GET(request: NextRequest) {
  const qs = new URL(request.url).searchParams.toString();
  const res = await fetch(`${BACKEND}/memory${qs ? `?${qs}` : ""}`);
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
