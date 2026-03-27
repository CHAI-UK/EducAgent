"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";

import { apiUrl, AUTH_TOKEN_KEY } from "@/lib/api";
import { hasAuthCookie } from "@/lib/auth-client";
import { Profile } from "@/types/profile";

function LoginForm() {
  const searchParams = useSearchParams();
  const { t } = useTranslation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [sessionExpired, setSessionExpired] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // AC3: redirect already-authenticated users to home (FR5d)
  // AC4: show session-expired message when redirected here with ?session_expired=1
  useEffect(() => {
    if (typeof window !== "undefined") {
      if (hasAuthCookie()) {
        window.location.href = "/";
        return;
      }
      if (searchParams.get("session_expired") === "1") {
        setSessionExpired(true);
      }
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSessionExpired(false);

    // Guard against a quick submit before the auth-redirect effect completes.
    if (typeof window !== "undefined" && hasAuthCookie()) {
      window.location.href = "/";
      return;
    }

    setIsSubmitting(true);

    try {
      // FastAPI-Users BearerTransport requires application/x-www-form-urlencoded
      // with field name "username" (OAuth2 spec) — NOT JSON
      const response = await fetch(apiUrl("/auth/jwt/login"), {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
        // Sync to cookie so Next.js Edge middleware can read it (localStorage is
        // not accessible on the server/Edge runtime).
        const secure = window.location.protocol === "https:" ? "; Secure" : "";
        document.cookie = `${AUTH_TOKEN_KEY}=${data.access_token}; path=/; SameSite=Lax${secure}`;

        // AC1: redirect to ?redirect= target (same-origin only) or home.
        // Hard-navigate (window.location.href) so the fresh auth cookie is
        // sent with the next request and the middleware cache is bypassed.
        const redirectTo = searchParams.get("redirect");
        const defaultRedirect =
          redirectTo && redirectTo.startsWith("/") ? redirectTo : "/";

        try {
          const profileResponse = await fetch(apiUrl("/api/v1/profile"), {
            headers: { Authorization: `Bearer ${data.access_token}` },
          });

          if (profileResponse.ok) {
            const profile = (await profileResponse.json()) as Profile;
            window.location.href = profile.learner_profile
              ? defaultRedirect
              : "/onboarding/learner";
            return;
          }
        } catch {
          // Fall back to the default redirect if the profile check fails.
        }

        window.location.href = defaultRedirect;
      } else {
        // AC2: display generic message — do not reveal which field failed
        setError(t("Invalid email or password"));
      }
    } catch {
      setError(t("Network error. Please check your connection and try again."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 px-4">
      <div className="w-full max-w-md p-8 bg-white dark:bg-slate-800 rounded-lg shadow">
        <h1 className="text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-2">
          {t("Sign in to EducAgent")}
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
          {t("Welcome back. Enter your credentials to continue.")}
        </p>

        {/* AC4: session expired banner */}
        {sessionExpired && (
          <div
            className="mb-4 px-4 py-3 rounded-md bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 text-sm text-amber-800 dark:text-amber-300"
            role="alert"
          >
            {t("Session expired, please log in again.")}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              {t("Email")}
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t("you@example.com")}
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              {t("Password")}
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t("Your password")}
            />
          </div>

          {/* AC2: error message */}
          {error && (
            <p className="text-sm text-red-500" role="alert">
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {isSubmitting ? t("Signing in...") : t("Sign in")}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
          {t("Don't have an account?")}{" "}
          <a href="/signup" className="text-blue-600 hover:underline">
            {t("Sign up")}
          </a>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
