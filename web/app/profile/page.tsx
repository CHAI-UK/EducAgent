"use client";

import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  BadgeCheck,
  BookOpenCheck,
  Building2,
  CalendarDays,
  Camera,
  CheckCircle2,
  KeyRound,
  Loader2,
  Mail,
  Save,
  ShieldCheck,
  UserCircle2,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { apiFetch, apiUrl } from "@/lib/api";
import { formatDate } from "@/lib/datetime";
import {
  buildLearnerProfileForm,
  getExpertiseLevelOptions,
  getPriorKnowledgeOptions,
  LearnerProfileFormState,
  togglePriorKnowledge,
  toLearnerProfilePayload,
} from "@/lib/learner-profile";
import { getProfileDisplayName, getProfileInitials } from "@/lib/profile";
import { useGlobal } from "@/context/GlobalContext";
import { Profile } from "@/types/profile";

interface ProfileFormState {
  username: string;
  first_name: string;
  last_name: string;
  institution: string;
}

interface PasswordFormState {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const EMPTY_PASSWORD_FORM: PasswordFormState = {
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
};

function StatusBadge({
  label,
  tone,
}: {
  label: string;
  tone: "blue" | "emerald" | "violet";
}) {
  const toneClasses =
    tone === "blue"
      ? "bg-blue-50 text-blue-700 ring-blue-200 dark:bg-blue-950/40 dark:text-blue-200 dark:ring-blue-900/80"
      : tone === "emerald"
        ? "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-200 dark:ring-emerald-900/80"
        : "bg-violet-50 text-violet-700 ring-violet-200 dark:bg-violet-950/40 dark:text-violet-200 dark:ring-violet-900/80";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset ${toneClasses}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

function buildProfileForm(profile: Profile): ProfileFormState {
  return {
    username: profile.username,
    first_name: profile.first_name ?? "",
    last_name: profile.last_name ?? "",
    institution: profile.institution ?? "",
  };
}

function learnerFormsEqual(
  left: LearnerProfileFormState,
  right: LearnerProfileFormState,
): boolean {
  return (
    left.background === right.background &&
    left.role === right.role &&
    left.learning_goal === right.learning_goal &&
    left.expertise_level === right.expertise_level &&
    left.prior_knowledge.length === right.prior_knowledge.length &&
    left.prior_knowledge.every(
      (item, index) => item === right.prior_knowledge[index],
    )
  );
}

export default function ProfilePage() {
  const { t } = useTranslation();
  const { uiSettings } = useGlobal();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeTab, setActiveTab] = useState<"account" | "learner">("account");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [form, setForm] = useState<ProfileFormState | null>(null);
  const [learnerForm, setLearnerForm] =
    useState<LearnerProfileFormState | null>(null);
  const [passwordForm, setPasswordForm] =
    useState<PasswordFormState>(EMPTY_PASSWORD_FORM);
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingLearnerProfile, setSavingLearnerProfile] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [updatingPassword, setUpdatingPassword] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [learnerMessage, setLearnerMessage] = useState<string | null>(null);
  const [learnerError, setLearnerError] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const priorKnowledgeOptions = useMemo(() => getPriorKnowledgeOptions(t), [t]);
  const expertiseLevelOptions = useMemo(() => getExpertiseLevelOptions(t), [t]);

  useEffect(() => {
    let mounted = true;

    apiFetch("/api/v1/profile")
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(t("Failed to load profile"));
        }
        return response.json();
      })
      .then((data: Profile) => {
        if (!mounted) return;
        setProfile(data);
        setForm(buildProfileForm(data));
        setLearnerForm(buildLearnerProfileForm(data.learner_profile));
      })
      .catch(() => {
        if (!mounted) return;
        setProfileError(t("We couldn't load your profile right now."));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [t]);

  useEffect(() => {
    return () => {
      if (avatarPreview?.startsWith("blob:")) {
        URL.revokeObjectURL(avatarPreview);
      }
    };
  }, [avatarPreview]);

  const baseLearnerForm = useMemo(
    () => buildLearnerProfileForm(profile?.learner_profile ?? null),
    [profile],
  );

  const isProfileDirty =
    !!profile &&
    !!form &&
    (profile.username !== form.username.trim() ||
      (profile.first_name ?? "") !== form.first_name.trim() ||
      (profile.last_name ?? "") !== form.last_name.trim() ||
      (profile.institution ?? "") !== form.institution.trim());

  const isLearnerDirty =
    !!learnerForm && !learnerFormsEqual(learnerForm, baseLearnerForm);

  const isProfileValid = !!form?.username.trim();
  const passwordMismatch =
    passwordForm.confirmPassword.length > 0 &&
    passwordForm.newPassword !== passwordForm.confirmPassword;
  const passwordTooShort =
    passwordForm.newPassword.length > 0 && passwordForm.newPassword.length < 8;
  const canSubmitPassword =
    passwordForm.currentPassword.length > 0 &&
    passwordForm.newPassword.length >= 8 &&
    passwordForm.confirmPassword.length > 0 &&
    !passwordMismatch;

  const displayName = useMemo(() => {
    if (!profile) return "";
    return getProfileDisplayName(profile);
  }, [profile]);

  const avatarFallback = useMemo(() => {
    if (!profile) return "";
    return getProfileInitials(profile);
  }, [profile]);

  const currentAvatar = avatarPreview ?? profile?.avatar_url ?? null;
  const joinedLabel =
    profile?.created_at != null
      ? formatDate(new Date(profile.created_at), uiSettings.language)
      : t("Unknown");
  const tabs = [
    {
      id: "account" as const,
      label: t("Account settings"),
      icon: <UserCircle2 className="h-4 w-4" />,
    },
    {
      id: "learner" as const,
      label: t("Learner profile"),
      icon: <BookOpenCheck className="h-4 w-4" />,
    },
  ];

  const syncProfile = (nextProfile: Profile) => {
    setProfile(nextProfile);
    setForm(buildProfileForm(nextProfile));
    setLearnerForm(buildLearnerProfileForm(nextProfile.learner_profile));
    window.dispatchEvent(
      new CustomEvent("profile-updated", { detail: nextProfile }),
    );
  };

  const handleProfileFieldChange = (
    field: keyof ProfileFormState,
    value: string,
  ) => {
    setForm((prev) => (prev ? { ...prev, [field]: value } : prev));
    setProfileMessage(null);
    setProfileError(null);
  };

  const handleLearnerFieldChange = <K extends keyof LearnerProfileFormState>(
    field: K,
    value: LearnerProfileFormState[K],
  ) => {
    setLearnerForm((prev) => (prev ? { ...prev, [field]: value } : prev));
    setLearnerMessage(null);
    setLearnerError(null);
  };

  const handleSaveProfile = async () => {
    if (!form || !isProfileValid || !isProfileDirty) return;

    setSavingProfile(true);
    setProfileMessage(null);
    setProfileError(null);

    try {
      const response = await apiFetch("/api/v1/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: form.username.trim(),
          first_name: form.first_name.trim() || null,
          last_name: form.last_name.trim() || null,
          institution: form.institution.trim() || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || t("Failed to save profile"));
      }

      const data = (await response.json()) as Profile;
      syncProfile(data);
      setProfileMessage(t("Profile details saved."));
    } catch (error) {
      setProfileError(
        error instanceof Error ? error.message : t("Failed to save profile"),
      );
    } finally {
      setSavingProfile(false);
    }
  };

  const handleSaveLearnerProfile = async () => {
    if (!learnerForm || !isLearnerDirty) return;

    setSavingLearnerProfile(true);
    setLearnerMessage(null);
    setLearnerError(null);

    try {
      const response = await apiFetch("/api/v1/profile/learner", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toLearnerProfilePayload(learnerForm)),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || t("Failed to save learner profile"),
        );
      }

      const data = (await response.json()) as Profile;
      syncProfile(data);
      setLearnerMessage(t("Learner profile saved."));
    } catch (error) {
      setLearnerError(
        error instanceof Error
          ? error.message
          : t("Failed to save learner profile"),
      );
    } finally {
      setSavingLearnerProfile(false);
    }
  };

  const handleAvatarSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (avatarPreview?.startsWith("blob:")) {
      URL.revokeObjectURL(avatarPreview);
    }

    setAvatarError(null);
    const previewUrl = URL.createObjectURL(file);
    setAvatarPreview(previewUrl);
    setUploadingAvatar(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await apiFetch("/api/v1/profile/avatar", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || t("Failed to upload avatar"));
      }

      const data = (await response.json()) as Profile;
      setAvatarPreview(null);
      syncProfile(data);
      setProfileMessage(t("Avatar updated."));
    } catch (error) {
      setAvatarPreview(null);
      setAvatarError(
        error instanceof Error ? error.message : t("Failed to upload avatar"),
      );
    } finally {
      setUploadingAvatar(false);
      event.target.value = "";
    }
  };

  const handlePasswordFieldChange = (
    field: keyof PasswordFormState,
    value: string,
  ) => {
    setPasswordForm((prev) => ({ ...prev, [field]: value }));
    setPasswordMessage(null);
    setPasswordError(null);
  };

  const handleUpdatePassword = async () => {
    if (!canSubmitPassword) return;

    setUpdatingPassword(true);
    setPasswordMessage(null);
    setPasswordError(null);

    try {
      const response = await apiFetch("/api/v1/profile/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || t("Failed to update password"));
      }

      setPasswordForm(EMPTY_PASSWORD_FORM);
      setPasswordMessage(t("Password updated."));
    } catch (error) {
      setPasswordError(
        error instanceof Error ? error.message : t("Failed to update password"),
      );
    } finally {
      setUpdatingPassword(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!profile || !form || !learnerForm) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 px-6 py-8">
        <div className="mx-auto max-w-5xl rounded-3xl border border-red-200 bg-white p-6 text-red-700 shadow-sm dark:border-red-900/60 dark:bg-slate-800 dark:text-red-300">
          {profileError ?? t("We couldn't load your profile right now.")}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="mx-auto max-w-6xl animate-fade-in p-6">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-blue-100 p-3 dark:bg-blue-900/30">
            <UserCircle2 className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {t("Profile")}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {t(
                "Manage your account details, learner profile, photo, and password.",
              )}
            </p>
          </div>
        </div>

        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-800">
          <div className="flex justify-center">
            <div className="flex max-w-3xl flex-col gap-5 sm:flex-row sm:items-center">
              <div className="relative">
                <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-2xl bg-blue-600 text-2xl font-semibold text-white">
                  {currentAvatar ? (
                    <img
                      src={
                        currentAvatar.startsWith("/api/")
                          ? apiUrl(currentAvatar)
                          : currentAvatar
                      }
                      alt={displayName}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    avatarFallback
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute -bottom-2 -right-2 inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  {uploadingAvatar ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Camera className="h-3.5 w-3.5" />
                  )}
                  {t("Upload")}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  className="hidden"
                  onChange={handleAvatarSelected}
                />
              </div>

              <div className="space-y-3">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
                    {displayName}
                  </h2>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    @{profile.username}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {profile.is_superuser && (
                    <StatusBadge label={t("Admin")} tone="violet" />
                  )}
                  {profile.is_verified && (
                    <StatusBadge label={t("Verified")} tone="blue" />
                  )}
                  {profile.is_active && (
                    <StatusBadge label={t("Active")} tone="emerald" />
                  )}
                </div>

                <div className="grid gap-2 text-sm text-slate-600 dark:text-slate-300">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-slate-400" />
                    <span>{profile.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-slate-400" />
                    <span>
                      {profile.institution ?? t("No institution added yet")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CalendarDays className="h-4 w-4 text-slate-400" />
                    <span>{t("Joined {{date}}", { date: joinedLabel })}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {avatarError && (
            <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
              {avatarError}
            </div>
          )}
        </section>

        <div className="flex gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-800 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-white text-blue-600 shadow-sm dark:bg-slate-700 dark:text-blue-400"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
          {activeTab === "account" && (
            <div className="grid gap-6 p-6 lg:grid-cols-[1.15fr_0.85fr]">
              <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
                <div className="mb-6 flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-950 dark:text-slate-50">
                      {t("Account settings")}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      {t(
                        "Keep your account details up to date. Changes are saved only when you confirm them.",
                      )}
                    </p>
                  </div>
                  {isProfileDirty && (
                    <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200 dark:bg-amber-950/40 dark:text-amber-200 dark:ring-amber-900/80">
                      {t("Unsaved changes")}
                    </span>
                  )}
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Username")}
                    <input
                      value={form.username}
                      onChange={(event) =>
                        handleProfileFieldChange("username", event.target.value)
                      }
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t("Username")}
                    />
                  </label>

                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Name")}
                    <input
                      value={form.first_name}
                      onChange={(event) =>
                        handleProfileFieldChange(
                          "first_name",
                          event.target.value,
                        )
                      }
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t("First name")}
                    />
                  </label>

                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Surname")}
                    <input
                      value={form.last_name}
                      onChange={(event) =>
                        handleProfileFieldChange(
                          "last_name",
                          event.target.value,
                        )
                      }
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t("Last name")}
                    />
                  </label>

                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Institution")}
                    <input
                      value={form.institution}
                      onChange={(event) =>
                        handleProfileFieldChange(
                          "institution",
                          event.target.value,
                        )
                      }
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t("Institution")}
                    />
                  </label>
                </div>

                <div className="mt-6 space-y-3">
                  {profileMessage && (
                    <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
                      <CheckCircle2 className="h-4 w-4" />
                      {profileMessage}
                    </div>
                  )}
                  {profileError && (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
                      {profileError}
                    </div>
                  )}
                </div>

                <div className="mt-6 flex justify-end border-t border-slate-200 pt-5 dark:border-slate-700">
                  <button
                    type="button"
                    onClick={handleSaveProfile}
                    disabled={
                      !isProfileDirty || !isProfileValid || savingProfile
                    }
                    className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700"
                  >
                    {savingProfile ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    {t("Save changes")}
                  </button>
                </div>
              </section>

              <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
                <div className="mb-5 flex items-start gap-3">
                  <div className="rounded-xl bg-blue-100 p-3 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300">
                    <KeyRound className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-slate-950 dark:text-slate-50">
                      {t("Password")}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      {t(
                        "Choose a new password carefully and confirm it before updating.",
                      )}
                    </p>
                  </div>
                </div>

                <div className="grid gap-4">
                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Current password")}
                    <input
                      type="password"
                      value={passwordForm.currentPassword}
                      onChange={(event) =>
                        handlePasswordFieldChange(
                          "currentPassword",
                          event.target.value,
                        )
                      }
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t("Current password")}
                    />
                  </label>

                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("New password")}
                    <input
                      type="password"
                      value={passwordForm.newPassword}
                      onChange={(event) =>
                        handlePasswordFieldChange(
                          "newPassword",
                          event.target.value,
                        )
                      }
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t("New password")}
                    />
                  </label>

                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Confirm new password")}
                    <input
                      type="password"
                      value={passwordForm.confirmPassword}
                      onChange={(event) =>
                        handlePasswordFieldChange(
                          "confirmPassword",
                          event.target.value,
                        )
                      }
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t("Confirm password")}
                    />
                  </label>
                </div>

                <div className="mt-4 space-y-3">
                  {passwordTooShort && (
                    <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
                      {t("New password must be at least 8 characters.")}
                    </div>
                  )}
                  {passwordMismatch && (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
                      {t("Password confirmation does not match.")}
                    </div>
                  )}
                  {passwordMessage && (
                    <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
                      <BadgeCheck className="h-4 w-4" />
                      {passwordMessage}
                    </div>
                  )}
                  {passwordError && (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
                      {passwordError}
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={handleUpdatePassword}
                  disabled={!canSubmitPassword || updatingPassword}
                  className="mt-5 inline-flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-white dark:disabled:bg-slate-700 dark:disabled:text-slate-300"
                >
                  {updatingPassword ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ShieldCheck className="h-4 w-4" />
                  )}
                  {t("Update password")}
                </button>
              </section>
            </div>
          )}

          {activeTab === "learner" && (
            <div className="p-6">
              <section className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
                <div className="mb-6 flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-xl bg-blue-100 p-3 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300">
                      <BookOpenCheck className="h-5 w-5" />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-slate-950 dark:text-slate-50">
                        {t("Learner profile")}
                      </h2>
                      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        {t(
                          "Update the context EducAgent uses to personalize your experience.",
                        )}
                      </p>
                    </div>
                  </div>
                  {isLearnerDirty && (
                    <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200 dark:bg-amber-950/40 dark:text-amber-200 dark:ring-amber-900/80">
                      {t("Unsaved changes")}
                    </span>
                  )}
                </div>

                {profile.learner_profile?.is_skipped && (
                  <div className="mb-5 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700 dark:border-blue-900/60 dark:bg-blue-950/30 dark:text-blue-300">
                    {t(
                      "You skipped setup earlier. Add your learner profile now any time.",
                    )}
                  </div>
                )}

                <div className="grid gap-5">
                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Background")}
                    <textarea
                      value={learnerForm.background}
                      onChange={(event) =>
                        handleLearnerFieldChange(
                          "background",
                          event.target.value,
                        )
                      }
                      rows={4}
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t(
                        "Computer scientist, clinician, statistician...",
                      )}
                    />
                  </label>

                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Role")}
                    <textarea
                      value={learnerForm.role}
                      onChange={(event) =>
                        handleLearnerFieldChange("role", event.target.value)
                      }
                      rows={3}
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t(
                        "PhD researcher, analyst, public health student...",
                      )}
                    />
                  </label>

                  <div className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    <span>{t("Prior knowledge")}</span>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {priorKnowledgeOptions.map((option) => {
                        const checked = learnerForm.prior_knowledge.includes(
                          option.value,
                        );
                        return (
                          <label
                            key={option.value}
                            className={`flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-sm transition ${
                              checked
                                ? "border-blue-300 bg-blue-50 text-blue-900 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-100"
                                : "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() =>
                                handleLearnerFieldChange(
                                  "prior_knowledge",
                                  togglePriorKnowledge(
                                    learnerForm.prior_knowledge,
                                    option.value,
                                  ),
                                )
                              }
                            />
                            <span>{option.label}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    <span>{t("Expertise level")}</span>
                    <div className="grid gap-3 sm:grid-cols-3">
                      {expertiseLevelOptions.map((option) => {
                        const checked =
                          learnerForm.expertise_level === option.value;
                        return (
                          <label
                            key={option.value}
                            className={`flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-sm transition ${
                              checked
                                ? "border-blue-300 bg-blue-50 text-blue-900 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-100"
                                : "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                            }`}
                          >
                            <input
                              type="radio"
                              name="profile-expertise-level"
                              checked={checked}
                              onChange={() =>
                                handleLearnerFieldChange(
                                  "expertise_level",
                                  option.value,
                                )
                              }
                            />
                            <span>{option.label}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                    {t("Learning goal")}
                    <textarea
                      value={learnerForm.learning_goal}
                      onChange={(event) =>
                        handleLearnerFieldChange(
                          "learning_goal",
                          event.target.value,
                        )
                      }
                      rows={4}
                      className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                      placeholder={t("Tell us what you want to learn next.")}
                    />
                  </label>
                </div>

                <div className="mt-6 space-y-3">
                  {learnerMessage && (
                    <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
                      <CheckCircle2 className="h-4 w-4" />
                      {learnerMessage}
                    </div>
                  )}
                  {learnerError && (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
                      {learnerError}
                    </div>
                  )}
                </div>

                <div className="mt-6 flex justify-end border-t border-slate-200 pt-5 dark:border-slate-700">
                  <button
                    type="button"
                    onClick={handleSaveLearnerProfile}
                    disabled={!isLearnerDirty || savingLearnerProfile}
                    className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700"
                  >
                    {savingLearnerProfile ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    {t("Save learner profile")}
                  </button>
                </div>
              </section>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
