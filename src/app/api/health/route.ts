import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    service: "frontend",
    status: "UP",
    checkedAt: new Date().toISOString(),
  });
}
