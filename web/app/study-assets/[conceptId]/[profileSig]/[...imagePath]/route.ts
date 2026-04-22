import fs from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

const CONTENT_ROOT = path.resolve(process.cwd(), "content", "study");
const ALLOWED_PROFILE_SIGS = new Set(["default", "bio", "cs", "econ"]);
const DEFAULT_PROFILE_SIG = "default";

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

function resolveImagePath(
  conceptId: string,
  profileSig: string,
  imagePath: string[],
) {
  const conceptRoot = path.resolve(CONTENT_ROOT, conceptId);
  const allowedConceptRoot = `${CONTENT_ROOT}${path.sep}`;

  if (
    conceptRoot !== CONTENT_ROOT &&
    !conceptRoot.startsWith(allowedConceptRoot)
  ) {
    return null;
  }

  const requestedPath = path.join(
    conceptRoot,
    profileSig,
    "imgs",
    ...imagePath,
  );
  const normalizedPath = path.normalize(requestedPath);
  const allowedRoot = path.join(conceptRoot, profileSig, "imgs") + path.sep;

  if (!normalizedPath.startsWith(allowedRoot)) {
    return null;
  }

  return normalizedPath;
}

export async function GET(
  _request: Request,
  context: {
    params: Promise<{
      conceptId: string;
      profileSig: string;
      imagePath: string[];
    }>;
  },
) {
  const { conceptId, profileSig, imagePath } = await context.params;

  if (!ALLOWED_PROFILE_SIGS.has(profileSig) || !imagePath.length) {
    return new NextResponse("Not found", { status: 404 });
  }

  const requestedPath = resolveImagePath(conceptId, profileSig, imagePath);
  if (!requestedPath) {
    return new NextResponse("Not found", { status: 404 });
  }

  try {
    const file = await fs.readFile(requestedPath);

    return new NextResponse(file, {
      headers: {
        "Content-Type": getContentType(requestedPath),
        "Cache-Control": "public, max-age=3600",
      },
    });
  } catch {
    if (profileSig === DEFAULT_PROFILE_SIG) {
      return new NextResponse("Not found", { status: 404 });
    }

    const fallbackPath = resolveImagePath(
      conceptId,
      DEFAULT_PROFILE_SIG,
      imagePath,
    );
    if (!fallbackPath) {
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
