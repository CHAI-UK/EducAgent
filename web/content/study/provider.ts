import "server-only";

import { cache } from "react";
import fs from "node:fs";
import path from "node:path";
import type { LearnerAdaptation, LearnerProfile } from "@/types/profile";

export type StudyContentSource = "static" | "generated";
export type StudyProfileSig = string;

export interface StudyNodeLink {
  relation: "previous" | "next";
  targetId: string;
}

export interface StudyQuizOption {
  id: string;
  label: string;
  text: string;
}

export interface StudyQuizQuestion {
  id: string;
  prompt: string;
  options: StudyQuizOption[];
  correctOptionId: string;
  explanation: string;
}

export interface StudySubtopic {
  id: string;
  title: string;
}

export interface StudyTopic {
  id: string;
  title: string;
}

export interface StudyNode {
  id: string;
  title: string;
  topic?: StudyTopic;
  content: string;
  order: number;
  subtopics?: StudySubtopic[];
  summary?: string;
  learningObjectives?: string[];
  imageRefs?: string[];
  links?: StudyNodeLink[];
  quiz?: StudyQuizQuestion[];
}

export interface StudyPath {
  id: string;
  title: string;
  source: StudyContentSource;
  conceptId: string;
  profileSig: StudyProfileSig;
  availableConcepts: StudyConceptSummary[];
  learnerProfile?: LearnerProfile | null;
  learnerAdaptation?: LearnerAdaptation | null;
  generatedAt?: string;
  nodes: StudyNode[];
}

export interface StudyConceptSummary {
  id: string;
  title: string;
}

export interface GetStudyPathOptions {
  conceptId?: string;
  learnerProfile?: LearnerProfile | null;
  learnerAdaptation?: LearnerAdaptation | null;
}

const STUDY_CONTENT_ROOT = path.resolve(process.cwd(), "content", "study");
const DEFAULT_PROFILE_SIG = "computer_science_ml";
const QUIZ_SECTION_TITLE = "Check Your Understanding";
const SAFE_PATH_SEGMENT = /^[A-Za-z0-9_-]+$/;
const STUDY_COURSES_BY_PROFILE = {
  computer_science_ml: ["directed-acyclic-graph-dag", "interventions"],
  radiologist: ["causal-discovery"],
  biologist: ["pc-algorithm"],
  material: ["directed-acyclic-graph-dag", "interventions"],
  education: ["directed-acyclic-graph-dag", "interventions"],
} as const satisfies Record<string, readonly string[]>;
type StudyConfiguredProfileSig = keyof typeof STUDY_COURSES_BY_PROFILE;

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function normalizeRequestedConceptId(conceptId?: string) {
  const normalized = conceptId?.trim();
  return normalized && isSafePathSegment(normalized) ? normalized : null;
}

function isConfiguredProfileSig(
  profileSig: string,
): profileSig is StudyConfiguredProfileSig {
  return Object.prototype.hasOwnProperty.call(
    STUDY_COURSES_BY_PROFILE,
    profileSig,
  );
}

function resolveStudyProfileSig(
  profileSig?: string | null,
): StudyConfiguredProfileSig {
  const normalizedProfileSig = profileSig?.trim();
  if (!normalizedProfileSig || !isSafePathSegment(normalizedProfileSig)) {
    return DEFAULT_PROFILE_SIG;
  }

  return isConfiguredProfileSig(normalizedProfileSig)
    ? normalizedProfileSig
    : DEFAULT_PROFILE_SIG;
}

function getConfiguredConceptIds(profileSig: StudyProfileSig): string[] {
  const resolvedProfileSig = resolveStudyProfileSig(profileSig);
  return [...STUDY_COURSES_BY_PROFILE[resolvedProfileSig]];
}

function getStudyProfileSigFromAdaptation(
  learnerAdaptation?: LearnerAdaptation | null,
): StudyProfileSig {
  return resolveStudyProfileSig(learnerAdaptation?.profile_sig);
}

function resolveConceptRoot(conceptId: string) {
  const conceptRoot = path.resolve(STUDY_CONTENT_ROOT, conceptId);
  const allowedRoot = `${STUDY_CONTENT_ROOT}${path.sep}`;

  if (
    conceptRoot !== STUDY_CONTENT_ROOT &&
    !conceptRoot.startsWith(allowedRoot)
  ) {
    throw new Error(`Invalid concept id: ${conceptId}`);
  }

  return conceptRoot;
}

function isSafePathSegment(value: string) {
  return SAFE_PATH_SEGMENT.test(value);
}

function resolveProfileRoot(conceptId: string, profileSig: StudyProfileSig) {
  const normalizedProfileSig = profileSig.trim();
  if (!normalizedProfileSig || !isSafePathSegment(normalizedProfileSig)) {
    return null;
  }

  const profileRoot = path.resolve(
    resolveConceptRoot(conceptId),
    normalizedProfileSig,
  );
  const conceptRoot = resolveConceptRoot(conceptId);
  const allowedRoot = `${conceptRoot}${path.sep}`;

  if (profileRoot !== conceptRoot && !profileRoot.startsWith(allowedRoot)) {
    return null;
  }

  return profileRoot;
}

function getMarkdownPathForProfileSig(
  conceptId: string,
  profileSig: StudyProfileSig,
) {
  const profileRoot = resolveProfileRoot(conceptId, profileSig);
  return profileRoot ? path.join(profileRoot, "content.md") : null;
}

function hasMarkdownForProfileSig(conceptId: string, profileSig: StudyProfileSig) {
  const markdownPath = getMarkdownPathForProfileSig(conceptId, profileSig);
  return Boolean(markdownPath && fs.existsSync(markdownPath));
}

function hasContentForConcept(conceptId: string, profileSig: StudyProfileSig) {
  return (
    hasMarkdownForProfileSig(conceptId, profileSig) ||
    hasMarkdownForProfileSig(conceptId, DEFAULT_PROFILE_SIG)
  );
}

function resolveAvailableConceptId(
  requestedConceptId: string | null,
  profileSig: StudyProfileSig,
) {
  const configuredConceptIds = getConfiguredConceptIds(profileSig);
  const allowedConceptIds = configuredConceptIds.filter((conceptId) =>
    hasContentForConcept(conceptId, profileSig),
  );

  if (!allowedConceptIds.length) {
    throw new Error(`No study content is available for profile "${profileSig}".`);
  }

  if (
    requestedConceptId &&
    configuredConceptIds.includes(requestedConceptId) &&
    hasContentForConcept(requestedConceptId, profileSig)
  ) {
    return requestedConceptId;
  }

  const fallbackConceptId = allowedConceptIds[0];

  if (requestedConceptId && requestedConceptId !== fallbackConceptId) {
    console.warn(
      `[study] Concept "${requestedConceptId}" is unavailable for profile "${profileSig}", falling back to "${fallbackConceptId}".`,
    );
  }

  return fallbackConceptId;
}

function resolveAvailableProfileSig(
  conceptId: string,
  profileSig: StudyProfileSig,
) {
  const requestedMarkdownPath = getMarkdownPathForProfileSig(
    conceptId,
    profileSig,
  );
  if (requestedMarkdownPath && fs.existsSync(requestedMarkdownPath)) {
    return profileSig;
  }

  if (profileSig !== DEFAULT_PROFILE_SIG) {
    console.warn(
      `[study] Missing content for profile_sig "${profileSig}" in concept "${conceptId}", falling back to "${DEFAULT_PROFILE_SIG}".`,
    );
  }

  return DEFAULT_PROFILE_SIG;
}

function getConceptTitle(conceptId: string, profileSig: StudyProfileSig) {
  const resolvedProfileSig = resolveAvailableProfileSig(conceptId, profileSig);
  const markdownPath = getMarkdownPathForProfileSig(
    conceptId,
    resolvedProfileSig,
  );
  if (!markdownPath || !fs.existsSync(markdownPath)) {
    return conceptId;
  }

  const markdown = fs.readFileSync(markdownPath, "utf8");
  return extractConceptTitle(markdown) ?? conceptId;
}

function extractConceptTitle(markdown: string) {
  const conceptMatch = markdown.match(
    /^\s*(?:\*\*)?Concept(?:\*\*)?\s*:\s*(?:\*\*)?(.+?)(?:\*\*)?\s*$/im,
  );
  if (conceptMatch?.[1]?.trim()) {
    return conceptMatch[1].trim();
  }

  const titleMatch = markdown.match(/^#\s+(.+)$/m);
  return titleMatch?.[1]?.trim();
}

function getAvailableConcepts(
  profileSig: StudyProfileSig,
): StudyConceptSummary[] {
  return getConfiguredConceptIds(profileSig)
    .filter((conceptId) => hasContentForConcept(conceptId, profileSig))
    .map((conceptId) => ({
      id: conceptId,
      title: getConceptTitle(conceptId, profileSig),
    }));
}

function rewriteImageSources(
  content: string,
  conceptId: string,
  profileSig: StudyProfileSig,
) {
  return content.replace(
    /!\[([^\]]*)\]\((imgs\/[^)]+)\)/g,
    (_match, altText: string, relativePath: string) =>
      `![${altText}](/study-assets/${conceptId}/${profileSig}/${relativePath.replace(/^imgs\//, "")})`,
  );
}

function extractLearningObjectives(content: string) {
  const lines = content.split("\n");
  const objectives: string[] = [];
  let capture = false;

  for (const line of lines) {
    if (!capture) {
      if (
        /^> By the end of this node, you will be able to:/.test(line.trim())
      ) {
        capture = true;
      }
      continue;
    }

    const trimmed = line.trim();
    if (!trimmed.startsWith(">")) {
      break;
    }

    const quoteContent = trimmed.replace(/^>\s*/, "").trim();
    if (!quoteContent) {
      continue;
    }

    const objective = quoteContent.replace(/^\d+\.\s*/, "").trim();
    if (objective) {
      objectives.push(objective);
    }
  }

  return objectives.length ? objectives : undefined;
}

function extractSummary(content: string) {
  const paragraphs = content
    .split(/\n\s*\n/)
    .map((block) => block.trim())
    .filter(Boolean)
    .filter(
      (block) =>
        !block.startsWith(">") &&
        !block.startsWith("```") &&
        !block.startsWith("![") &&
        !block.startsWith("<details>") &&
        !block.startsWith("---") &&
        !block.startsWith("##") &&
        !block.startsWith("###"),
    );

  return paragraphs[0];
}

function extractImageRefs(content: string) {
  const matches = content.match(/!\[[^\]]*\]\(([^)]+)\)/g) ?? [];
  const refs = matches
    .map((match) => match.match(/\(([^)]+)\)/)?.[1])
    .filter((value): value is string => Boolean(value));

  return refs.length ? refs : undefined;
}

function extractSubtopics(content: string) {
  const subtopics = [...content.matchAll(/^###\s+(.+)$/gm)].map((match) => {
    const title = match[1].trim();

    return {
      id: slugify(title),
      title,
    } satisfies StudySubtopic;
  });

  return subtopics.length ? subtopics : undefined;
}

function parseQuizQuestions(
  quizMarkdown: string,
  answerMap: Map<
    string,
    {
      correctOptionId: string;
      explanation: string;
    }
  >,
) {
  const questionMatches = [
    ...quizMarkdown.matchAll(
      /^\s*(?:\*\*)?(\d+)[.)](?:\*\*)?\s+([\s\S]*?)(?=^\s*(?:\*\*)?\d+[.)](?:\*\*)?\s+|(?![\s\S]))/gm,
    ),
  ];

  const questions = questionMatches
    .map((match) => {
      const questionNumber = match[1];
      const rawBlock = match[2].trim();
      const inlineAnswerMatch = rawBlock.match(
        /<details>[\s\S]*?<summary>[\s\S]*?<\/summary>\s*([\s\S]*?)<\/details>/i,
      );
      const inlineAnswer = inlineAnswerMatch
        ? parseQuizAnswerBlock(inlineAnswerMatch[1], questionNumber)
        : null;
      const block = inlineAnswerMatch
        ? rawBlock.replace(inlineAnswerMatch[0], "").trim()
        : rawBlock;
      const lines = block
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);

      if (!lines.length) {
        return null;
      }

      const promptLines: string[] = [];
      const options: StudyQuizOption[] = [];

      for (const line of lines) {
        const optionMatch = line.match(/^(?:-\s*)?([A-Da-d])(?:\)|\.)\s+(.+)$/);
        if (optionMatch) {
          options.push({
            id: optionMatch[1].toUpperCase(),
            label: optionMatch[1].toUpperCase(),
            text: optionMatch[2].trim(),
          });
          continue;
        }

        if (!options.length) {
          promptLines.push(line);
        }
      }

      const answer = inlineAnswer ?? answerMap.get(questionNumber);
      if (!answer || !options.length) {
        return null;
      }

      return {
        id: `q${questionNumber}`,
        prompt: promptLines.join(" ").trim(),
        options,
        correctOptionId: answer.correctOptionId,
        explanation: answer.explanation,
      } satisfies StudyQuizQuestion;
    })
    .filter((question): question is StudyQuizQuestion => Boolean(question));

  return questions.length ? questions : undefined;
}

function cleanQuizExplanation(value: string) {
  return value
    .replace(/^\s*\*\*?\s*/, "")
    .replace(/\*\*?\s*$/, "")
    .replace(/^[.)\s—-]+/, "")
    .trim();
}

function parseQuizAnswerBlock(markdown: string, fallbackQuestionNumber?: string) {
  const answerMatch = markdown.match(
    /(?:Question\s+(\d+)\s*[—-]\s*)?(?:Correct answer|Answer):\s*([A-Da-d])(?:[.)])?/i,
  );

  if (!answerMatch) {
    return null;
  }

  const questionNumber = answerMatch[1] ?? fallbackQuestionNumber;
  if (!questionNumber) {
    return null;
  }

  const explanation = cleanQuizExplanation(
    markdown.slice((answerMatch.index ?? 0) + answerMatch[0].length),
  );

  return {
    questionNumber,
    correctOptionId: answerMatch[2].toUpperCase(),
    explanation,
  };
}

function parseQuizAnswers(answerMarkdown: string) {
  const answerMap = new Map<
    string,
    { correctOptionId: string; explanation: string }
  >();
  const headerPattern =
    /(?:^|\n)\s*(?:\*\*)?(?:(?:Question|Answer|Answer\s+to\s+Question)\s+)?(\d+)(?:\.|:|\s*[—-]\s*)\s*(?:(?:Correct answer|Answer):\s*)?(?:\*\*)?([A-Da-d])(?:[.)])?(?:\*\*)?/g;
  const answerHeaders = [...answerMarkdown.matchAll(headerPattern)];

  if (answerHeaders.length) {
    answerHeaders.forEach((match, index) => {
      const nextMatch = answerHeaders[index + 1];
      const explanationStart = (match.index ?? 0) + match[0].length;
      const explanationEnd = nextMatch?.index ?? answerMarkdown.length;

      answerMap.set(match[1], {
        correctOptionId: match[2].toUpperCase(),
        explanation: cleanQuizExplanation(
          answerMarkdown.slice(explanationStart, explanationEnd),
        ),
      });
    });

    return answerMap;
  }

  for (const rawLine of answerMarkdown.split("\n")) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }

    const match = line.match(
      /^(?:\*\*)?(?:(?:Question|Answer|Answer\s+to\s+Question)\s+)?(\d+)(?:\.|:)\s*(?:Answer:\s*)?(?:\*\*)?([A-Da-d])(?:\)|\.)?(?:\*\*)?\s*(?:[—-]\s*)?(.+)$/,
    );
    if (!match) {
      continue;
    }

    answerMap.set(match[1], {
      correctOptionId: match[2].toUpperCase(),
      explanation: match[3].trim(),
    });
  }

  return answerMap;
}

function extractQuiz(content: string) {
  const quizHeadingMatch = content.match(
    new RegExp(`^##\\s+${QUIZ_SECTION_TITLE}\\s*$`, "m"),
  );

  if (!quizHeadingMatch || quizHeadingMatch.index === undefined) {
    return { content, quiz: undefined as StudyQuizQuestion[] | undefined };
  }

  const quizBlockStart = quizHeadingMatch.index + quizHeadingMatch[0].length;
  const contentBeforeQuiz = content.slice(0, quizHeadingMatch.index).trim();
  const quizBlock = content.slice(quizBlockStart).trim();
  const answerDetailsMatch = quizBlock.match(
    /<details>[\s\S]*?<summary>\s*([^<]+?)\s*<\/summary>\s*([\s\S]*?)<\/details>/i,
  );
  const answerSummary = answerDetailsMatch?.[1].trim().toLowerCase() ?? "";
  const hasGlobalAnswerDetails = Boolean(
    answerDetailsMatch &&
      (answerSummary.includes("answers") ||
        answerSummary.includes("answer key") ||
        answerSummary.includes("explanations")),
  );
  const questionMarkdown =
    hasGlobalAnswerDetails && answerDetailsMatch
      ? quizBlock.slice(0, answerDetailsMatch.index ?? 0).trim()
      : quizBlock;
  const answerMarkdown =
    hasGlobalAnswerDetails && answerDetailsMatch
      ? answerDetailsMatch[2].trim()
      : "";
  const answerMap = parseQuizAnswers(answerMarkdown);
  const quiz = parseQuizQuestions(questionMarkdown, answerMap);
  const contentWithoutQuiz = contentBeforeQuiz.replace(/\n{3,}/g, "\n\n");

  return {
    content: contentWithoutQuiz,
    quiz,
  };
}

interface SectionMatch {
  title: string;
  index: number;
  length: number;
}

interface TopicMatch extends SectionMatch {
  id: string;
}

function getTopicForSection(section: SectionMatch, topics: TopicMatch[]) {
  let topic: TopicMatch | undefined;

  for (const candidateTopic of topics) {
    if (candidateTopic.index > section.index) {
      break;
    }

    topic = candidateTopic;
  }

  return topic
    ? {
        id: topic.id,
        title: topic.title,
      }
    : undefined;
}

function buildLinkedNodes(
  sections: SectionMatch[],
  topics: TopicMatch[],
  markdown: string,
  conceptId: string,
) {
  const nodes = sections.map((section, index) => {
    const bodyStart = section.index + section.length + 1;
    const sectionEnd =
      index + 1 < sections.length
        ? sections[index + 1].index - 1
        : markdown.length;
    const rawContent = markdown.slice(bodyStart, sectionEnd).trim();

    return {
      section,
      topic: getTopicForSection(section, topics),
      rawContent,
    };
  });

  const mergedNodes: Array<{
    title: string;
    topic?: StudyTopic;
    content: string;
  }> = [];

  for (const node of nodes) {
    if (!node.rawContent) {
      continue;
    }

    mergedNodes.push({
      title: node.section.title,
      topic: node.topic,
      content: node.rawContent,
    });
  }

  const parsedNodes = mergedNodes.map((node, index) => {
    const contentToParse =
      node.title === QUIZ_SECTION_TITLE
        ? `## ${QUIZ_SECTION_TITLE}\n\n${node.content}`
        : node.content;
    const { content, quiz } = extractQuiz(contentToParse);

    return {
      id: `${conceptId}-node-${index + 1}-${slugify(node.title)}`,
      title: node.title,
      topic: node.topic,
      content,
      order: index + 1,
      subtopics: extractSubtopics(content),
      summary: extractSummary(content),
      learningObjectives: extractLearningObjectives(content),
      imageRefs: extractImageRefs(content),
      quiz,
    } satisfies StudyNode;
  });

  return parsedNodes.map((node, index) => {
    const links: StudyNodeLink[] = [];

    if (index > 0) {
      links.push({ relation: "previous", targetId: parsedNodes[index - 1].id });
    }
    if (index < parsedNodes.length - 1) {
      links.push({ relation: "next", targetId: parsedNodes[index + 1].id });
    }

    return {
      ...node,
      links: links.length ? links : undefined,
    };
  });
}

function parseStudyMarkdown(
  markdown: string,
  conceptId: string,
  profileSig: StudyProfileSig,
): StudyPath {
  const normalizedMarkdown = rewriteImageSources(
    markdown.trim(),
    conceptId,
    profileSig,
  );
  const pathTitle = extractConceptTitle(normalizedMarkdown) ?? conceptId;
  const headingMatches = [...normalizedMarkdown.matchAll(/^##\s+(.+)$/gm)].map(
    (match) => ({
      title: match[1].trim(),
      index: match.index ?? 0,
      length: match[0].length,
    }),
  );
  const topicMatches = [
    ...normalizedMarkdown.matchAll(/^#\s+(?!#)(.+)$/gm),
  ].map((match) => {
    const title = match[1].trim();

    return {
      id: slugify(title),
      title,
      index: match.index ?? 0,
      length: match[0].length,
    } satisfies TopicMatch;
  });

  if (!headingMatches.length) {
    throw new Error(
      "Study content must include at least one '##' section heading.",
    );
  }

  const linkedNodes = buildLinkedNodes(
    headingMatches,
    topicMatches,
    normalizedMarkdown,
    conceptId,
  );

  return {
    id: conceptId,
    title: pathTitle,
    source: "static",
    conceptId,
    profileSig,
    availableConcepts: [],
    nodes: linkedNodes,
  };
}

const loadStaticStudyPath = cache(
  (requestedConceptId: string | null, profileSig: StudyProfileSig) => {
    const resolvedConceptId = resolveAvailableConceptId(
      requestedConceptId,
      profileSig,
    );
    const resolvedProfileSig = resolveAvailableProfileSig(
      resolvedConceptId,
      profileSig,
    );
    const markdownPath = getMarkdownPathForProfileSig(
      resolvedConceptId,
      resolvedProfileSig,
    );
    if (!markdownPath) {
      throw new Error(`Invalid study profile signature: ${resolvedProfileSig}`);
    }
    const markdown = fs.readFileSync(markdownPath, "utf8");
    const studyPath = parseStudyMarkdown(
      markdown,
      resolvedConceptId,
      resolvedProfileSig,
    );

    return {
      ...studyPath,
      availableConcepts: getAvailableConcepts(profileSig),
    };
  },
);

export async function getStudyPath(
  options: GetStudyPathOptions = {},
): Promise<StudyPath> {
  const profileSig = getStudyProfileSigFromAdaptation(
    options.learnerAdaptation,
  );
  const conceptId = normalizeRequestedConceptId(options.conceptId);
  const studyPath = loadStaticStudyPath(conceptId, profileSig);

  return {
    ...studyPath,
    learnerProfile: options.learnerProfile ?? null,
    learnerAdaptation: options.learnerAdaptation ?? null,
  };
}
