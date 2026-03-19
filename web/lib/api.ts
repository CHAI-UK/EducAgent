// API configuration and utility functions

// JWT token localStorage key — shared by login, signup, and apiFetch
export const AUTH_TOKEN_KEY = "educagent_access_token";

// Get API base URL from environment variable
// This is automatically set by start_web.py based on config/main.yaml
// The .env.local file is auto-generated on startup with the correct backend port
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE ||
  (() => {
    if (typeof window !== "undefined") {
      console.error("NEXT_PUBLIC_API_BASE is not set.");
      console.error(
        "Please configure server ports in config/main.yaml and restart the application using: python scripts/start_web.py",
      );
      console.error(
        "The .env.local file will be automatically generated with the correct backend port.",
      );
    }
    // No fallback - port must be configured in config/main.yaml
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
 * Fetch wrapper that intercepts 401 responses (expired/invalid JWT) and
 * redirects to /login?session_expired=1, clearing the stored token first.
 */
export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const response = await fetch(apiUrl(path), init);
  if (response.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem(AUTH_TOKEN_KEY);
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

  return `${normalizedBase}${normalizedPath}`;
}
