/**
 * Session by ID API Route - Proxy to FastAPI backend
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND = "http://localhost:8000";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const res = await fetch(`${BACKEND}/sessions/${id}`);
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function PATCH(
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
          `[sessions PATCH] Invalid JSON body (Fail Fast)\n` +
          `  id: ${id}\n` +
          `  Error: ${e instanceof Error ? e.message : String(e)}`,
      },
      { status: 400 }
    );
  }
  const res = await fetch(`${BACKEND}/sessions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const res = await fetch(`${BACKEND}/sessions/${id}`, { method: "DELETE" });
  if (res.status === 204) return new NextResponse(null, { status: 204 });
  let data: unknown;
  try {
    data = await res.json();
  } catch (e) {
    return NextResponse.json(
      {
        detail:
          `[sessions DELETE] Non-JSON response (Fail Fast)\n` +
          `  id: ${id}\n` +
          `  Status: ${res.status}\n` +
          `  Error: ${e instanceof Error ? e.message : String(e)}`,
      },
      { status: 502 }
    );
  }
  return NextResponse.json(data, { status: res.status });
}
