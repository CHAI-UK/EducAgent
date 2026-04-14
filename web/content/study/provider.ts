import "server-only";

import { cache } from "react";
import fs from "node:fs";
import path from "node:path";
import type { LearnerProfile } from "@/types/profile";

export type StudyContentSource = "static" | "generated";
export type StudyVariant = "default" | "bio" | "cs" | "econ";

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

export interface StudyNode {
  id: string;
  title: string;
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
  variant: StudyVariant;
  learnerProfile?: LearnerProfile | null;
  generatedAt?: string;
  nodes: StudyNode[];
}

export interface GetStudyPathOptions {
  learnerProfile?: LearnerProfile | null;
}

const COUNTERFACTUALS_CONTENT_ROOT = path.resolve(
  process.cwd(),
  "content",
  "study",
  "counterfactuals",
);
const DEFAULT_STUDY_VARIANT: StudyVariant = "default";
const STUDY_VARIANTS: StudyVariant[] = ["default", "bio", "cs", "econ"];
const QUIZ_SECTION_TITLE = "Check Your Understanding";

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function getStudyVariantFromLearnerProfile(
  learnerProfile?: LearnerProfile | null,
): StudyVariant {
  const background = learnerProfile?.background?.trim().toLowerCase();
  if (!background) {
    return DEFAULT_STUDY_VARIANT;
  }

  if (
    /(economics|economist|economic|policy|public policy|finance|financial)/.test(
      background,
    )
  ) {
    return "econ";
  }

  if (
    /(computer science|computing|software|programming|engineer|engineering|ai|a\.?i\.?|ml|machine learning|data science)/.test(
      background,
    )
  ) {
    return "cs";
  }

  if (
    /(biology|biologist|bioinformatics|biomedical|medicine|medical|health|healthcare|neuroscience|neuro|genetics|life science)/.test(
      background,
    )
  ) {
    return "bio";
  }

  return DEFAULT_STUDY_VARIANT;
}

function getMarkdownPathForVariant(variant: StudyVariant) {
  return path.join(COUNTERFACTUALS_CONTENT_ROOT, variant, "content.md");
}

function resolveAvailableVariant(variant: StudyVariant) {
  const requestedMarkdownPath = getMarkdownPathForVariant(variant);
  if (fs.existsSync(requestedMarkdownPath)) {
    return variant;
  }

  if (variant !== DEFAULT_STUDY_VARIANT) {
    console.warn(
      `[study] Missing content for variant "${variant}", falling back to "${DEFAULT_STUDY_VARIANT}".`,
    );
  }

  return DEFAULT_STUDY_VARIANT;
}

function rewriteImageSources(content: string, variant: StudyVariant) {
  return content.replace(
    /!\[([^\]]*)\]\((imgs\/[^)]+)\)/g,
    (_match, altText: string, relativePath: string) =>
      `![${altText}](/study-assets/${variant}/${relativePath.replace(/^imgs\//, "")})`,
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
      /\*\*(\d+)\.\*\*\s+([\s\S]*?)(?=(?:\n\*\*\d+\.\*\*\s)|$)/g,
    ),
  ];

  const questions = questionMatches
    .map((match) => {
      const questionNumber = match[1];
      const block = match[2].trim();
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

      const answer = answerMap.get(questionNumber);
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

function parseQuizAnswers(answerMarkdown: string) {
  const answerMap = new Map<
    string,
    { correctOptionId: string; explanation: string }
  >();
  const lines = answerMarkdown.split("\n");

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }

    const match = line.match(
      /^(?:\*\*)?(\d+)\.\s*(?:Answer:\s*)?(?:\*\*)?([A-Da-d])(?:\)|\.)?(?:\*\*)?\s*(?:[—-]\s*)?(.+)$/,
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
  const quizSectionMatch = content.match(
    new RegExp(
      `## ${QUIZ_SECTION_TITLE}\\s*([\\s\\S]*?)<details>[\\s\\S]*?<summary>[\\s\\S]*?<\\/summary>\\s*([\\s\\S]*?)<\\/details>`,
    ),
  );

  if (!quizSectionMatch) {
    return { content, quiz: undefined as StudyQuizQuestion[] | undefined };
  }

  const questionMarkdown = quizSectionMatch[1].trim();
  const answerMarkdown = quizSectionMatch[2].trim();
  const answerMap = parseQuizAnswers(answerMarkdown);
  const quiz = parseQuizQuestions(questionMarkdown, answerMap);
  const contentWithoutQuiz = content
    .replace(quizSectionMatch[0], "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

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

function buildLinkedNodes(sections: SectionMatch[], markdown: string) {
  const nodes = sections.map((section, index) => {
    const bodyStart = section.index + section.length + 1;
    const sectionEnd =
      index + 1 < sections.length
        ? sections[index + 1].index - 1
        : markdown.length;
    const rawContent = markdown.slice(bodyStart, sectionEnd).trim();

    return {
      section,
      rawContent,
    };
  });

  const mergedNodes: Array<{
    title: string;
    content: string;
  }> = [];

  for (const node of nodes) {
    if (node.section.title === QUIZ_SECTION_TITLE && mergedNodes.length > 0) {
      const previousNode = mergedNodes[mergedNodes.length - 1];
      previousNode.content =
        `${previousNode.content}\n\n## ${QUIZ_SECTION_TITLE}\n\n${node.rawContent}`.trim();
      continue;
    }

    mergedNodes.push({
      title: node.section.title,
      content: node.rawContent,
    });
  }

  const parsedNodes = mergedNodes.map((node, index) => {
    const { content, quiz } = extractQuiz(node.content);

    return {
      id: `counterfactual-node-${index + 1}-${slugify(node.title)}`,
      title: node.title,
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

function parseCounterfactualMarkdown(
  markdown: string,
  variant: StudyVariant,
): StudyPath {
  const normalizedMarkdown = rewriteImageSources(markdown.trim(), variant);
  const titleMatch = normalizedMarkdown.match(/^#\s+(.+)$/m);
  const pathTitle = titleMatch?.[1]?.trim() ?? "Counterfactuals";
  const headingMatches = [...normalizedMarkdown.matchAll(/^##\s+(.+)$/gm)].map(
    (match) => ({
      title: match[1].trim(),
      index: match.index ?? 0,
      length: match[0].length,
    }),
  );

  if (!headingMatches.length) {
    throw new Error(
      "Study content must include at least one '##' section heading.",
    );
  }

  const linkedNodes = buildLinkedNodes(headingMatches, normalizedMarkdown);

  return {
    id: "counterfactuals",
    title: pathTitle,
    source: "static",
    variant,
    nodes: linkedNodes,
  };
}

const loadStaticStudyPath = cache((variant: StudyVariant) => {
  const resolvedVariant = resolveAvailableVariant(variant);
  const markdownPath = getMarkdownPathForVariant(resolvedVariant);
  const markdown = fs.readFileSync(markdownPath, "utf8");
  return parseCounterfactualMarkdown(markdown, resolvedVariant);
});

export async function getStudyPath(
  options: GetStudyPathOptions = {},
): Promise<StudyPath> {
  const variant = getStudyVariantFromLearnerProfile(options.learnerProfile);
  const studyPath = loadStaticStudyPath(variant);

  return {
    ...studyPath,
    learnerProfile: options.learnerProfile ?? null,
  };
}
