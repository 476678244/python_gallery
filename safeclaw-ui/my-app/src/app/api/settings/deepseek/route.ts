import { NextResponse } from "next/server";
const BACKEND = "http://localhost:8000";

export async function GET() {
  const res = await fetch(`${BACKEND}/settings/deepseek`);
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function PUT(request: Request) {
  const body = await request.json();
  const res = await fetch(`${BACKEND}/settings/deepseek`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
