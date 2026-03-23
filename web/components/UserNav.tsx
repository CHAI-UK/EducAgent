"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { LogOut, User } from "lucide-react";
import { apiUrl, apiFetch, AUTH_TOKEN_KEY } from "@/lib/api";

const PUBLIC_PATHS = new Set(["/login", "/signup"]);

interface UserInfo {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
}

export default function UserNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch current user on mount (skip on public pages like /login, /signup)
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (PUBLIC_PATHS.has(pathname)) return;
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return;

    apiFetch("/users/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data: UserInfo | null) => {
        if (data) setUser(data);
      })
      .catch(() => {
        // Silently fail — apiFetch already handles 401 → redirects to /login
      });
  }, [pathname]);

  // Close dropdown on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleLogout = () => {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem(AUTH_TOKEN_KEY)
        : null;

    // Clear local state FIRST so the redirect is immediate — don't wait for
    // the backend round-trip which can take seconds.
    if (typeof window !== "undefined") {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      const secure =
        window.location.protocol === "https:" ? "; Secure" : "";
      document.cookie = `${AUTH_TOKEN_KEY}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax${secure}`;
    }

    // Fire-and-forget server-side token invalidation (best-effort)
    if (token) {
      fetch(apiUrl("/auth/jwt/logout"), {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }

    // Hard-navigate immediately — flushes client cache + forces middleware check.
    window.location.href = "/login";
  };

  // Don't render until user data is available
  if (!user) return null;

  const initial = user.username.charAt(0).toUpperCase();

  return (
    <div ref={containerRef} className="relative flex items-center">
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-2 px-2 py-1.5 rounded-md text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        aria-label="User menu"
        aria-haspopup="true"
        aria-expanded={open}
      >
        {/* Circular avatar with initial */}
        <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-semibold flex-shrink-0">
          {initial}
        </div>
        {/* Username — hide on very small screens */}
        <span className="hidden sm:block text-sm font-medium max-w-[120px] truncate">
          {user.username}
        </span>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-1 w-44 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md shadow-lg z-50 py-1"
          role="menu"
        >
          <Link
            href="/profile"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
          >
            <User className="w-4 h-4 text-slate-400" />
            View Profile
          </Link>
          <button
            role="menuitem"
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-slate-700 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      )}
    </div>
  );
}
