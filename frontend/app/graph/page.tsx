"use client";

import { useRouter } from "next/navigation";

import KnowledgeGraph from "@/components/graph/knowledge_graph";

export default function GraphPage() {
  const router = useRouter();

  return (
    <div className="flex h-screen flex-col bg-zinc-50">
      {/* Header */}
      <div className="flex items-center gap-4 border-b border-zinc-200 bg-white px-8 py-5">
        <button
          onClick={() => router.push("/")}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900"
          aria-label="Back to chat"
        >
          ←
        </button>

        <div>
          <h1 className="text-xl font-semibold text-zinc-900">
            Knowledge Graph
          </h1>

          <p className="mt-1 text-sm text-zinc-500">
            Explore how your knowledge and concepts are connected.
          </p>
        </div>
      </div>

      {/* Graph */}
      <div className="min-h-0 flex-1">
        <KnowledgeGraph />
      </div>
    </div>
  );
}