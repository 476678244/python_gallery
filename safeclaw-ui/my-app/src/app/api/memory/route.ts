import { NextResponse } from "next/server";
const BACKEND = "http://localhost:8000";

export async function GET() {
  const res = await fetch(`${BACKEND}/memory`);
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
