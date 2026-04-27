"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import type { StudyPath } from "@/content/study";
import courseGraph from "./course-graph.json";

interface KnowledgeGraphPageClientProps {
  studyPath: StudyPath;
}

interface CourseNode {
  id: string;
  label: string;
}

interface CourseEdge {
  from: string;
  to: string;
}

interface PositionedCourseNode extends CourseNode {
  x: number;
  y: number;
}

const COURSE_NODES: CourseNode[] = courseGraph.nodes;
const COURSE_EDGES: CourseEdge[] = courseGraph.edges;
const NODE_RADIUS = 68;
const GRAPH_WIDTH = 760;
const GRAPH_HEIGHT = 360;
const HORIZONTAL_PADDING = 110;
const VERTICAL_PADDING = 85;

function buildCourseLayout() {
  const nodeIds = new Set(COURSE_NODES.map((node) => node.id));
  const incomingByNode = new Map<string, string[]>(
    COURSE_NODES.map((node) => [node.id, []]),
  );
  const depthByNode = new Map<string, number>();

  for (const edge of COURSE_EDGES) {
    if (!nodeIds.has(edge.from) || !nodeIds.has(edge.to)) {
      throw new Error(`Invalid course graph edge: ${edge.from} -> ${edge.to}`);
    }

    incomingByNode.get(edge.to)?.push(edge.from);
  }

  function getDepth(nodeId: string, visiting = new Set<string>()): number {
    const cachedDepth = depthByNode.get(nodeId);
    if (cachedDepth !== undefined) {
      return cachedDepth;
    }

    if (visiting.has(nodeId)) {
      throw new Error(`Course graph contains a cycle at "${nodeId}".`);
    }

    visiting.add(nodeId);
    const incoming = incomingByNode.get(nodeId) ?? [];
    const depth = incoming.length
      ? Math.max(...incoming.map((parentId) => getDepth(parentId, visiting))) +
        1
      : 0;
    visiting.delete(nodeId);
    depthByNode.set(nodeId, depth);
    return depth;
  }

  for (const node of COURSE_NODES) {
    getDepth(node.id);
  }

  const columns = new Map<number, CourseNode[]>();
  for (const node of COURSE_NODES) {
    const depth = depthByNode.get(node.id) ?? 0;
    columns.set(depth, [...(columns.get(depth) ?? []), node]);
  }

  const maxDepth = Math.max(...depthByNode.values(), 0);
  const horizontalStep =
    maxDepth > 0 ? (GRAPH_WIDTH - HORIZONTAL_PADDING * 2) / maxDepth : 0;
  const positionedNodes = new Map<string, PositionedCourseNode>();

  for (const [depth, nodes] of columns) {
    const availableHeight = GRAPH_HEIGHT - VERTICAL_PADDING * 2;
    const verticalStep =
      nodes.length > 1 ? availableHeight / (nodes.length - 1) : 0;
    const startY = nodes.length > 1 ? VERTICAL_PADDING : GRAPH_HEIGHT / 2;

    nodes.forEach((node, index) => {
      positionedNodes.set(node.id, {
        ...node,
        x: HORIZONTAL_PADDING + horizontalStep * depth,
        y: startY + verticalStep * index,
      });
    });
  }

  return positionedNodes;
}

const POSITIONED_COURSE_NODES = buildCourseLayout();

function getNode(id: string) {
  const node = POSITIONED_COURSE_NODES.get(id);
  if (!node) {
    throw new Error(`Unknown course node: ${id}`);
  }
  return node;
}

function getEdgePoints(edge: CourseEdge) {
  const from = getNode(edge.from);
  const to = getNode(edge.to);
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const distance = Math.hypot(dx, dy);
  const offsetX = (dx / distance) * NODE_RADIUS;
  const offsetY = (dy / distance) * NODE_RADIUS;

  return {
    x1: from.x + offsetX,
    y1: from.y + offsetY,
    x2: to.x - offsetX,
    y2: to.y - offsetY,
  };
}

export default function KnowledgeGraphPageClient({
  studyPath,
}: KnowledgeGraphPageClientProps) {
  const { t } = useTranslation();
  const availableConceptIds = new Set(
    studyPath.availableConcepts.map((concept) => concept.id),
  );

  return (
    <div className="min-h-screen p-4">
      <div className="mx-auto max-w-6xl">
        <div className="mb-4">
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
            {t("Knowledge Graph")}
          </h1>
        </div>

        <section className="min-h-[440px] overflow-x-auto rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800 md:p-8">
          <div
            className="relative mx-auto"
            style={{
              height: `${GRAPH_HEIGHT}px`,
              width: `${GRAPH_WIDTH}px`,
            }}
            aria-label={t("Knowledge Graph")}
          >
            <svg
              aria-hidden="true"
              className="absolute inset-0 h-full w-full"
              viewBox={`0 0 ${GRAPH_WIDTH} ${GRAPH_HEIGHT}`}
            >
              {COURSE_EDGES.map((edge) => {
                const points = getEdgePoints(edge);

                return (
                  <line
                    key={`${edge.from}-${edge.to}`}
                    x1={points.x1}
                    y1={points.y1}
                    x2={points.x2}
                    y2={points.y2}
                    stroke="currentColor"
                    strokeWidth="4"
                    strokeLinecap="round"
                    className="text-slate-900 dark:text-slate-100"
                  />
                );
              })}
            </svg>

            {[...POSITIONED_COURSE_NODES.values()].map((node) => {
              const isEnabled = availableConceptIds.has(node.id);
              const commonClassName =
                "absolute flex h-[136px] w-[136px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-4 text-center text-sm font-semibold transition-colors";
              const style = {
                left: `${node.x}px`,
                top: `${node.y}px`,
              };

              if (!isEnabled) {
                return (
                  <button
                    key={node.id}
                    type="button"
                    disabled
                    aria-disabled="true"
                    title={t("Not available for your profile")}
                    className={`${commonClassName} cursor-not-allowed border-slate-300 bg-slate-100 text-slate-400 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-500`}
                    style={style}
                  >
                    {node.label}
                  </button>
                );
              }

              return (
                <Link
                  key={node.id}
                  href={`/study?concept=${encodeURIComponent(node.id)}`}
                  className={`${commonClassName} border-slate-900 bg-white text-slate-950 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-indigo-500 dark:border-slate-100 dark:bg-slate-800 dark:text-white dark:hover:bg-slate-700`}
                  style={style}
                >
                  {node.label}
                </Link>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
