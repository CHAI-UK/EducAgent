"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiUrl, AUTH_TOKEN_KEY } from "@/lib/api";
import { hasAuthCookie } from "@/lib/auth-client";

type ValidationErrorDetail = {
  msg?: string;
  loc?: Array<string | number>;
};

function getRegistrationErrorMessage(detail: unknown): string {
  if (typeof detail === "string" && detail.trim().length > 0) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }

        const error = item as ValidationErrorDetail;
        if (typeof error.msg !== "string" || error.msg.trim().length === 0) {
          return null;
        }

        const field = error.loc?.[error.loc.length - 1];
        if (typeof field === "string" && field !== "body") {
          const label = field.charAt(0).toUpperCase() + field.slice(1);
          return `${label}: ${error.msg}`;
        }

        return error.msg;
      })
      .filter((message): message is string => Boolean(message));

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return "Registration failed. Please try again.";
}

export default function SignupPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");
  const [serverError, setServerError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // AC4: redirect already-authenticated users to home (FR5d)
  useEffect(() => {
    if (typeof window !== "undefined") {
      if (hasAuthCookie()) {
        router.replace("/");
      }
    }
  }, [router]);

  // AC3: inline password-length validation
  const validateConfirmPassword = (
    nextPassword: string,
    nextConfirmPassword: string,
  ) => {
    if (
      nextConfirmPassword.length > 0 &&
      nextPassword !== nextConfirmPassword
    ) {
      setConfirmPasswordError("Passwords do not match");
    } else {
      setConfirmPasswordError("");
    }
  };

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    if (value.length > 0 && value.length < 8) {
      setPasswordError("Password must be at least 8 characters");
    } else {
      setPasswordError("");
    }

    validateConfirmPassword(value, confirmPassword);
  };

  const handleConfirmPasswordChange = (value: string) => {
    setConfirmPassword(value);
    validateConfirmPassword(password, value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError("");

    const normalizedEmail = email.trim().toLowerCase();
    const normalizedUsername = username.trim();

    // Client-side guard before submitting
    if (!normalizedEmail) {
      setServerError("Email is required");
      return;
    }

    if (!normalizedUsername) {
      setServerError("Username is required");
      return;
    }

    if (password.length < 8) {
      setPasswordError("Password must be at least 8 characters");
      return;
    }

    if (password !== confirmPassword) {
      setConfirmPasswordError("Passwords do not match");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(apiUrl("/auth/register"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: normalizedEmail,
          username: normalizedUsername,
          password,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (response.status === 201) {
        // AC1: successful registration → redirect to home
        // (profile wizard is Story 2 — redirected there once implemented)
        router.push("/");
      } else if (response.status === 400) {
        // AC2: duplicate email
        if (typeof data.detail === "string") {
          setServerError(
            data.detail === "REGISTER_USER_ALREADY_EXISTS"
              ? "An account with this email already exists"
              : data.detail,
          );
        } else {
          setServerError("An account with this email already exists");
        }
      } else {
        setServerError(getRegistrationErrorMessage(data.detail));
      }
    } catch {
      setServerError(
        "Network error. Please check your connection and try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 px-4">
      <div className="w-full max-w-md p-8 bg-white dark:bg-slate-800 rounded-lg shadow">
        <h1 className="text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-2">
          Create your account
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
          Join EducAgent and start your learning journey.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="you@example.com"
            />
          </div>

          {/* Username */}
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Choose a username"
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="new-password"
              value={password}
              onChange={(e) => handlePasswordChange(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="At least 8 characters"
            />
            {/* AC3: inline password-length error */}
            {passwordError && (
              <p className="mt-1 text-sm text-red-500" role="alert">
                {passwordError}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="confirm-password"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Confirm password
            </label>
            <input
              id="confirm-password"
              type="password"
              required
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => handleConfirmPasswordChange(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Retype your password"
            />
            {confirmPasswordError && (
              <p className="mt-1 text-sm text-red-500" role="alert">
                {confirmPasswordError}
              </p>
            )}
          </div>

          {/* Server error (AC2 + general) */}
          {serverError && (
            <p className="text-sm text-red-500" role="alert">
              {serverError}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {isSubmitting ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
          Already have an account?{" "}
          <a href="/login" className="text-blue-600 hover:underline">
            Sign in
          </a>
        </p>
      </div>
    </div>
  );
}
