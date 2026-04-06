// API configuration and utility functions

export { AUTH_TOKEN_KEY } from "./auth-constants";
import { AUTH_TOKEN_KEY } from "./auth-constants";

const LOCAL_API_FALLBACK = "http://localhost:8001";

// Get API base URL from environment variable
// This is automatically set by start_web.py based on config/main.yaml
// The .env.local file is auto-generated on startup with the correct backend port
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE ||
  (() => {
    const isLocalDevOrTest = process.env.NODE_ENV !== "production";

    if (isLocalDevOrTest) {
      if (typeof window !== "undefined") {
        console.warn(
          `NEXT_PUBLIC_API_BASE is not set. Falling back to ${LOCAL_API_FALLBACK} for local development/testing.`,
        );
      }
      return LOCAL_API_FALLBACK;
    }

    if (typeof window !== "undefined") {
      console.error("NEXT_PUBLIC_API_BASE is not set.");
      console.error(
        "Please configure server ports in config/main.yaml and restart the application using: python scripts/start_web.py",
      );
      console.error(
        "The .env.local file will be automatically generated with the correct backend port.",
      );
    }
    // Keep production fail-closed so deployments don't accidentally point to localhost.
    throw new Error(
      "NEXT_PUBLIC_API_BASE is not configured. Please set server ports in config/main.yaml and restart.",
    );
  })();

/**
 * Construct a full API URL from a path
 * @param path - API path (e.g., '/api/v1/knowledge/list')
 * @returns Full URL (e.g., 'http://localhost:8000/api/v1/knowledge/list')
 */
export function apiUrl(path: string): string {
  // Remove leading slash if present to avoid double slashes
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  // Remove trailing slash from base URL if present
  const base = API_BASE_URL.endsWith("/")
    ? API_BASE_URL.slice(0, -1)
    : API_BASE_URL;

  return `${base}${normalizedPath}`;
}

/**
 * Fetch wrapper that:
 * - Automatically injects the stored JWT as an Authorization: Bearer header
 *   (callers that pass their own Authorization header take precedence)
 * - Intercepts 401 responses (expired/invalid JWT) and redirects to
 *   /login?session_expired=1, clearing the stored token first.
 */
export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  // Auto-inject auth token if available and caller hasn't provided their own
  let headers = new Headers(init?.headers);
  if (!headers.has("Authorization") && typeof window !== "undefined") {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(apiUrl(path), { ...init, headers });
  if (response.status === 401 && typeof window !== "undefined") {
    // Skip redirect if already on a public page to avoid infinite reload loop
    // (e.g. GlobalContext fetches settings on /login with no token → 401)
    const publicPaths = new Set(["/login", "/signup"]);
    if (publicPaths.has(window.location.pathname)) {
      return response;
    }
    localStorage.removeItem(AUTH_TOKEN_KEY);
    // Expire the middleware cookie in sync with localStorage
    const secure = window.location.protocol === "https:" ? "; Secure" : "";
    document.cookie = `${AUTH_TOKEN_KEY}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax${secure}`;
    window.location.href = "/login?session_expired=1";
    // Never resolve — navigation is in progress; prevents callers from
    // double-handling the 401 response body after the redirect fires.
    return new Promise(() => {});
  }
  return response;
}

/**
 * Construct a WebSocket URL from a path
 * @param path - WebSocket path (e.g., '/api/v1/solve')
 * @returns WebSocket URL (e.g., 'ws://localhost:{backend_port}/api/v1/solve')
 * Note: backend_port is configured in config/main.yaml
 */
export function wsUrl(path: string): string {
  // Security Hardening: Convert http to ws and https to wss.
  // In production environments (where API_BASE_URL starts with https), this ensures secure websockets.
  const base = API_BASE_URL.replace(/^http:/, "ws:").replace(/^https:/, "wss:");

  // Remove leading slash if present to avoid double slashes
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  // Remove trailing slash from base URL if present
  const normalizedBase = base.endsWith("/") ? base.slice(0, -1) : base;

  const url = new URL(`${normalizedBase}${normalizedPath}`);

  if (typeof window !== "undefined") {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      url.searchParams.set("access_token", token);
    }
  }

  return url.toString();
}
