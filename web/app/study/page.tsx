import { Suspense } from "react";
import { cookies } from "next/headers";
import { AUTH_TOKEN_KEY } from "@/lib/auth-constants";
import { apiUrl } from "@/lib/api";
import { getStudyPath } from "@/content/study";
import type { Profile } from "@/types/profile";
import StudyPageClient from "./StudyPageClient";

async function getCurrentLearnerProfile() {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_TOKEN_KEY)?.value;

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(apiUrl("/api/v1/profile"), {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const profile = (await response.json()) as Profile;
    return profile.learner_profile ?? null;
  } catch {
    return null;
  }
}

export default async function StudyPage() {
  const learnerProfile = await getCurrentLearnerProfile();
  const studyPath = await getStudyPath({
    learnerProfile,
  });

  return (
    <Suspense fallback={<div className="h-screen p-4" />}>
      <StudyPageClient studyPath={studyPath} />
    </Suspense>
  );
}
