import { NextResponse } from "next/server";
const BACKEND = "http://localhost:8000";

export async function POST() {
  const res = await fetch(`${BACKEND}/memory/cleanup`, { method: "POST" });
  const data = await res.json().catch(() => ({ success: true }));
  return NextResponse.json(data, { status: res.status });
}
