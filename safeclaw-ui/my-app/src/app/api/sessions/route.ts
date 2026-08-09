/**
 * Sessions API Route - Proxy to FastAPI backend
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND = "http://localhost:8000";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const qs = searchParams.toString();
  const res = await fetch(`${BACKEND}/sessions${qs ? `?${qs}` : ""}`, {
    headers: { "Content-Type": "application/json" },
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch (e) {
    return NextResponse.json(
      {
        detail:
          `[sessions POST] Invalid JSON body (Fail Fast)\n` +
          `  Error: ${e instanceof Error ? e.message : String(e)}`,
      },
      { status: 400 }
    );
  }
  const res = await fetch(`${BACKEND}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function DELETE(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) {
    return NextResponse.json(
      { detail: "[sessions DELETE] Missing query param id (Fail Fast)" },
      { status: 400 }
    );
  }
  const res = await fetch(`${BACKEND}/sessions?id=${id}`, {
    method: "DELETE",
  });
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return new NextResponse(null, { status: 204 });
  }
  let data: unknown;
  try {
    data = await res.json();
  } catch (e) {
    return NextResponse.json(
      {
        detail:
          `[sessions DELETE] Non-JSON response (Fail Fast)\n` +
          `  Status: ${res.status}\n` +
          `  Error: ${e instanceof Error ? e.message : String(e)}`,
      },
      { status: 502 }
    );
  }
  return NextResponse.json(data, { status: res.status });
}
