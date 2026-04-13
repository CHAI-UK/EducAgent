import "server-only";

import { cache } from "react";
import fs from "node:fs";
import path from "node:path";
import type { LearnerProfile } from "@/types/profile";

export type StudyContentSource = "static" | "generated";

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

export interface StudyNode {
  id: string;
  title: string;
  content: string;
  order: number;
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
  learnerProfile?: LearnerProfile | null;
  generatedAt?: string;
  nodes: StudyNode[];
}

export interface GetStudyPathOptions {
  learnerProfile?: LearnerProfile | null;
}

const COUNTERFACTUALS_MARKDOWN_PATH = path.resolve(
  process.cwd(),
  "content",
  "study",
  "counterfactuals",
  "content.md",
);

const PUBLIC_IMAGE_PREFIX = "/study-assets/counterfactuals";
const COUNTERFACTUAL_NODE_TITLES = [
  "What If? The Power of Counterfactual Thinking",
  "What SCMs Give Us — and Why You Need Them",
  "What Would Have Happened? Walking Through a Real Example",
  "What If We Could Rewind the Tape?",
  "Counterfactuals in Policy Evaluation: Why This Matters for Economics",
] as const;

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function rewriteImageSources(content: string) {
  return content.replace(
    /!\[([^\]]*)\]\((imgs\/[^)]+)\)/g,
    (_match, altText: string, relativePath: string) =>
      `![${altText}](${PUBLIC_IMAGE_PREFIX}/${relativePath.replace(/^imgs\//, "")})`,
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
        const optionMatch = line.match(/^-\s*([A-Da-d])\)\s+(.+)$/);
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
      /^(?:\*\*)?(\d+)\.\s*(?:Answer:\s*)?(?:\*\*)?([A-Da-d])(?:\*\*)?\)?\s*[—-]\s*(.+?)(?:\*\*)?$/,
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
    /## Check Your Understanding\s*([\s\S]*?)<details>[\s\S]*?<summary>[\s\S]*?<\/summary>\s*([\s\S]*?)<\/details>/,
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

function parseCounterfactualMarkdown(markdown: string): StudyPath {
  const normalizedMarkdown = rewriteImageSources(markdown.trim());
  const titleMatch = normalizedMarkdown.match(/^#\s+(.+)$/m);
  const pathTitle = titleMatch?.[1]?.trim() ?? "Counterfactuals";
  const headingMatches = COUNTERFACTUAL_NODE_TITLES.map((nodeTitle) => {
    const escapedTitle = nodeTitle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`^##\\s+${escapedTitle}$`, "m");
    const match = regex.exec(normalizedMarkdown);

    if (!match || typeof match.index !== "number") {
      throw new Error(`Missing counterfactual node heading: ${nodeTitle}`);
    }

    return {
      title: nodeTitle,
      index: match.index,
      length: match[0].length,
    };
  });

  const nodes = headingMatches.map((match, index) => {
    const title = match.title;
    const sectionStart = match.index;
    const bodyStart = sectionStart + match.length + 1;
    const sectionEnd =
      index + 1 < headingMatches.length
        ? headingMatches[index + 1].index - 1
        : normalizedMarkdown.length;
    const rawContent = normalizedMarkdown.slice(bodyStart, sectionEnd).trim();
    const { content, quiz } = extractQuiz(rawContent);

    return {
      id: `counterfactual-node-${index + 1}-${slugify(title)}`,
      title,
      content,
      order: index + 1,
      summary: extractSummary(content),
      learningObjectives: extractLearningObjectives(content),
      imageRefs: extractImageRefs(content),
      quiz,
    } satisfies StudyNode;
  });

  const linkedNodes = nodes.map((node, index) => {
    const links: StudyNodeLink[] = [];

    if (index > 0) {
      links.push({ relation: "previous", targetId: nodes[index - 1].id });
    }
    if (index < nodes.length - 1) {
      links.push({ relation: "next", targetId: nodes[index + 1].id });
    }

    return {
      ...node,
      links: links.length ? links : undefined,
    };
  });

  return {
    id: "counterfactuals",
    title: pathTitle,
    source: "static",
    nodes: linkedNodes,
  };
}

const loadStaticStudyPath = cache(() => {
  const markdown = fs.readFileSync(COUNTERFACTUALS_MARKDOWN_PATH, "utf8");
  return parseCounterfactualMarkdown(markdown);
});

export async function getStudyPath(
  options: GetStudyPathOptions = {},
): Promise<StudyPath> {
  const studyPath = loadStaticStudyPath();

  return {
    ...studyPath,
    learnerProfile: options.learnerProfile ?? null,
  };
}
