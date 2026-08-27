"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeProps,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

type KnowledgeNodeData = {
  title: string;
  description?: string;
  mastery: number;
  confidence: number;
};

type KnowledgeGraphNode = Node<KnowledgeNodeData>;

function getMasteryLabel(mastery: number) {
  if (mastery >= 0.8) return "Strong";
  if (mastery >= 0.6) return "Good";
  if (mastery >= 0.4) return "Developing";
  return "Needs work";
}

function KnowledgeNodeComponent({
  data,
  selected,
}: NodeProps<KnowledgeGraphNode>) {
  const masteryPercent = Math.round(data.mastery * 100);
  const confidencePercent = Math.round(data.confidence * 100);

  return (
    <div
      className={`
        min-w-[220px]
        rounded-2xl
        border
        bg-white
        shadow-lg
        transition-all
        duration-200
        dark:bg-zinc-900
        ${
          selected
            ? "border-blue-500 shadow-blue-500/20 shadow-xl"
            : "border-zinc-200 dark:border-zinc-700"
        }
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-2 !border-white !bg-zinc-400"
      />

      <div className="px-4 pt-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">
              {data.title}
            </h3>

            <p className="mt-1 text-[11px] text-zinc-500">
              {getMasteryLabel(data.mastery)}
            </p>
          </div>

          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800">
            <span className="text-xs font-bold text-zinc-700 dark:text-zinc-200">
              {masteryPercent}%
            </span>
          </div>
        </div>
      </div>

      <div className="px-4 pb-4 pt-3">
        {/* Mastery */}
        <div>
          <div className="mb-1 flex justify-between text-[10px] text-zinc-500">
            <span>Mastery</span>
            <span>{masteryPercent}%</span>
          </div>

          <div className="h-1.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
            <div
              className="h-full rounded-full bg-blue-500 transition-all"
              style={{
                width: `${masteryPercent}%`,
              }}
            />
          </div>
        </div>

        {/* Confidence */}
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-[10px] text-zinc-500">
            <span>Confidence</span>
            <span>{confidencePercent}%</span>
          </div>

          <div className="h-1 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
            <div
              className="h-full rounded-full bg-zinc-400"
              style={{
                width: `${confidencePercent}%`,
              }}
            />
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-2 !border-white !bg-blue-500"
      />
    </div>
  );
}

const nodeTypes = {
  knowledge: KnowledgeNodeComponent,
};

function buildInitialNodes(): KnowledgeGraphNode[] {
  return [
    {
      id: "programming",
      type: "knowledge",
      position: { x: 50, y: 50 },
      data: {
        title: "Programming Fundamentals",
        description:
          "Core programming concepts including variables, loops, conditions and functions.",
        mastery: 0.95,
        confidence: 0.98,
      },
    },

    {
      id: "python",
      type: "knowledge",
      position: { x: 50, y: 250 },
      data: {
        title: "Python",
        description:
          "Programming language used for software development, data science and AI.",
        mastery: 0.9,
        confidence: 0.95,
      },
    },

    {
      id: "data-structures",
      type: "knowledge",
      position: { x: 50, y: 450 },
      data: {
        title: "Data Structures",
        description:
          "Methods for organizing and storing data efficiently.",
        mastery: 0.72,
        confidence: 0.8,
      },
    },

    {
      id: "linear-algebra",
      type: "knowledge",
      position: { x: 400, y: 50 },
      data: {
        title: "Linear Algebra",
        description:
          "Vectors, matrices and linear transformations.",
        mastery: 0.65,
        confidence: 0.75,
      },
    },

    {
      id: "calculus",
      type: "knowledge",
      position: { x: 650, y: 50 },
      data: {
        title: "Calculus",
        description:
          "Derivatives, integrals and continuous change.",
        mastery: 0.58,
        confidence: 0.7,
      },
    },

    {
      id: "probability",
      type: "knowledge",
      position: { x: 900, y: 50 },
      data: {
        title: "Probability",
        description:
          "Mathematical reasoning about uncertainty and random events.",
        mastery: 0.62,
        confidence: 0.72,
      },
    },

    {
      id: "statistics",
      type: "knowledge",
      position: { x: 1150, y: 50 },
      data: {
        title: "Statistics",
        description:
          "Methods for analyzing and interpreting data.",
        mastery: 0.7,
        confidence: 0.78,
      },
    },

    {
      id: "machine-learning",
      type: "knowledge",
      position: { x: 650, y: 300 },
      data: {
        title: "Machine Learning",
        description:
          "Learning patterns from data to make predictions or decisions.",
        mastery: 0.55,
        confidence: 0.65,
      },
    },

    {
      id: "neural-networks",
      type: "knowledge",
      position: { x: 650, y: 520 },
      data: {
        title: "Neural Networks",
        description:
          "Machine learning models inspired by biological neural networks.",
        mastery: 0.42,
        confidence: 0.55,
      },
    },

    {
      id: "deep-learning",
      type: "knowledge",
      position: { x: 650, y: 740 },
      data: {
        title: "Deep Learning",
        description:
          "Machine learning based on multi-layer neural networks.",
        mastery: 0.35,
        confidence: 0.48,
      },
    },

    {
      id: "computer-vision",
      type: "knowledge",
      position: { x: 400, y: 950 },
      data: {
        title: "Computer Vision",
        description:
          "AI techniques for understanding visual information.",
        mastery: 0.3,
        confidence: 0.4,
      },
    },

    {
      id: "nlp",
      type: "knowledge",
      position: { x: 900, y: 950 },
      data: {
        title: "Natural Language Processing",
        description:
          "AI techniques for understanding and generating human language.",
        mastery: 0.45,
        confidence: 0.52,
      },
    },
  ];
}

function buildInitialEdges(): Edge[] {
  return [
    {
      id: "programming-python",
      source: "programming",
      target: "python",
      animated: true,
    },

    {
      id: "python-data",
      source: "python",
      target: "data-structures",
    },

    {
      id: "linear-ml",
      source: "linear-algebra",
      target: "machine-learning",
    },

    {
      id: "calculus-ml",
      source: "calculus",
      target: "machine-learning",
    },

    {
      id: "probability-ml",
      source: "probability",
      target: "machine-learning",
    },

    {
      id: "statistics-ml",
      source: "statistics",
      target: "machine-learning",
    },

    {
      id: "ml-neural",
      source: "machine-learning",
      target: "neural-networks",
    },

    {
      id: "neural-deep",
      source: "neural-networks",
      target: "deep-learning",
    },

    {
      id: "deep-cv",
      source: "deep-learning",
      target: "computer-vision",
    },

    {
      id: "deep-nlp",
      source: "deep-learning",
      target: "nlp",
    },
  ];
}

export default function KnowledgeGraph() {
  const [nodes, setNodes, onNodesChange] =
    useNodesState<KnowledgeGraphNode>(buildInitialNodes());

  const [edges, setEdges, onEdgesChange] =
    useEdgesState<Edge>(buildInitialEdges());

  const [selectedNode, setSelectedNode] =
    useState<KnowledgeGraphNode | null>(null);

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: KnowledgeGraphNode) => {
      setSelectedNode(node);
    },
    []
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const minimapNodeColor = useCallback((node: Node) => {
    const mastery = node.data?.mastery ?? 0;

    if (mastery >= 0.8) return "#22c55e";
    if (mastery >= 0.6) return "#eab308";
    if (mastery >= 0.4) return "#f97316";

    return "#ef4444";
  }, []);

  return (
    <div className="relative h-full w-full overflow-hidden rounded-3xl border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        fitViewOptions={{
          padding: 0.2,
        }}
        minZoom={0.2}
        maxZoom={2}
        defaultEdgeOptions={{
          type: "smoothstep",
          animated: false,
          style: {
            strokeWidth: 2,
          },
        }}
        proOptions={{
          hideAttribution: true,
        }}
      >
        <Background gap={24} size={1} />

        <Controls
          showInteractive={false}
          className="!rounded-xl !border !border-zinc-200 !bg-white !shadow-md dark:!border-zinc-700 dark:!bg-zinc-900"
        />

        <MiniMap
          nodeColor={minimapNodeColor}
          pannable
          zoomable
          className="!overflow-hidden !rounded-xl !border !border-zinc-200 dark:!border-zinc-700"
        />
      </ReactFlow>

      {/* Header */}
      <div className="pointer-events-none absolute left-5 top-5 z-10">
        <div className="rounded-2xl border border-zinc-200 bg-white/90 px-4 py-3 shadow-sm backdrop-blur dark:border-zinc-700 dark:bg-zinc-900/90">
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-white">
            Knowledge Graph
          </h2>

          <p className="mt-1 text-xs text-zinc-500">
            Drag nodes to explore your learning journey
          </p>
        </div>
      </div>

      {/* Selected node panel */}
      {selectedNode && (
        <div className="absolute right-5 top-5 z-20 w-80 rounded-2xl border border-zinc-200 bg-white p-5 shadow-xl dark:border-zinc-700 dark:bg-zinc-900">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-zinc-900 dark:text-white">
                {selectedNode.data.title}
              </h3>

              <p className="mt-1 text-xs text-zinc-500">
                Knowledge Concept
              </p>
            </div>

            <button
              onClick={() => setSelectedNode(null)}
              className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800"
            >
              ✕
            </button>
          </div>

          {selectedNode.data.description && (
            <p className="mt-4 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
              {selectedNode.data.description}
            </p>
          )}

          <div className="mt-5">
            <div className="flex justify-between text-xs">
              <span className="text-zinc-500">Mastery</span>

              <span className="font-semibold text-zinc-900 dark:text-white">
                {Math.round(selectedNode.data.mastery * 100)}%
              </span>
            </div>

            <div className="mt-2 h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
              <div
                className="h-full rounded-full bg-blue-500"
                style={{
                  width: `${selectedNode.data.mastery * 100}%`,
                }}
              />
            </div>
          </div>

          <div className="mt-4">
            <div className="flex justify-between text-xs">
              <span className="text-zinc-500">Confidence</span>

              <span className="font-semibold text-zinc-900 dark:text-white">
                {Math.round(selectedNode.data.confidence * 100)}%
              </span>
            </div>

            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
              <div
                className="h-full rounded-full bg-zinc-400"
                style={{
                  width: `${selectedNode.data.confidence * 100}%`,
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}