import { NextRequest, NextResponse } from "next/server";
const BACKEND = "http://localhost:8000";

/** Recursively convert snake_case keys to camelCase */
function snakeToCamel(obj: unknown): unknown {
  if (Array.isArray(obj)) {
    return obj.map(snakeToCamel);
  }
  if (obj !== null && typeof obj === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      const camelKey = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
      result[camelKey] = snakeToCamel(value);
    }
    return result;
  }
  return obj;
}

export async function GET() {
  const res = await fetch(`${BACKEND}/skills`);
  const data = await res.json();
  return NextResponse.json(snakeToCamel(data), { status: res.status });
}

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch (e) {
    return NextResponse.json(
      {
        detail:
          `[skills POST] Invalid JSON body (Fail Fast)\n` +
          `  Error: ${e instanceof Error ? e.message : String(e)}`,
      },
      { status: 400 }
    );
  }
  const res = await fetch(`${BACKEND}/skills`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
