import { Suspense } from "react";
import { getStudyPath } from "@/content/study";
import StudyPageClient from "./StudyPageClient";

export default async function StudyPage() {
  const studyPath = await getStudyPath();

  return (
    <Suspense fallback={<div className="h-screen p-4" />}>
      <StudyPageClient studyPath={studyPath} />
    </Suspense>
  );
}
