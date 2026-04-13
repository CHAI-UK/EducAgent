import { getStudyPath } from "@/content/study";
import KnowledgeGraphPageClient from "./KnowledgeGraphPageClient";

export default async function KnowledgeGraphPage() {
  const studyPath = await getStudyPath();

  return <KnowledgeGraphPageClient studyPath={studyPath} />;
}
