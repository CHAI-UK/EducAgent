import fs from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

const CONTENT_ROOT = path.resolve(
  process.cwd(),
  "content",
  "study",
  "counterfactuals",
);
const ALLOWED_VARIANTS = new Set(["default", "bio", "cs", "econ"]);
const DEFAULT_VARIANT = "default";

function getContentType(filePath: string) {
  const extension = path.extname(filePath).toLowerCase();

  switch (extension) {
    case ".png":
      return "image/png";
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".webp":
      return "image/webp";
    case ".gif":
      return "image/gif";
    case ".svg":
      return "image/svg+xml";
    default:
      return "application/octet-stream";
  }
}

export async function GET(
  _request: Request,
  context: {
    params: Promise<{
      variant: string;
      imagePath: string[];
    }>;
  },
) {
  const { variant, imagePath } = await context.params;

  if (!ALLOWED_VARIANTS.has(variant) || !imagePath.length) {
    return new NextResponse("Not found", { status: 404 });
  }

  const requestedPath = path.join(CONTENT_ROOT, variant, "imgs", ...imagePath);
  const normalizedPath = path.normalize(requestedPath);
  const allowedRoot = path.join(CONTENT_ROOT, variant, "imgs") + path.sep;

  if (!normalizedPath.startsWith(allowedRoot)) {
    return new NextResponse("Not found", { status: 404 });
  }

  try {
    const file = await fs.readFile(normalizedPath);

    return new NextResponse(file, {
      headers: {
        "Content-Type": getContentType(normalizedPath),
        "Cache-Control": "public, max-age=3600",
      },
    });
  } catch {
    if (variant === DEFAULT_VARIANT) {
      return new NextResponse("Not found", { status: 404 });
    }

    const fallbackPath = path.normalize(
      path.join(CONTENT_ROOT, DEFAULT_VARIANT, "imgs", ...imagePath),
    );
    const fallbackRoot =
      path.join(CONTENT_ROOT, DEFAULT_VARIANT, "imgs") + path.sep;

    if (!fallbackPath.startsWith(fallbackRoot)) {
      return new NextResponse("Not found", { status: 404 });
    }

    try {
      const fallbackFile = await fs.readFile(fallbackPath);

      return new NextResponse(fallbackFile, {
        headers: {
          "Content-Type": getContentType(fallbackPath),
          "Cache-Control": "public, max-age=3600",
        },
      });
    } catch {
      return new NextResponse("Not found", { status: 404 });
    }
  }
}
