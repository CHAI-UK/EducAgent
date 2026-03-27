"use client";

import { AUTH_TOKEN_KEY } from "./auth-constants";

export function hasAuthCookie(): boolean {
  if (typeof document === "undefined") return false;
  const cookiePrefix = `${AUTH_TOKEN_KEY}=`;
  return document.cookie.split("; ").some((cookie) => {
    return cookie.startsWith(cookiePrefix);
  });
}
