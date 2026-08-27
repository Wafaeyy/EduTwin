const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export type KnowledgeGraphNode = {
  id: string;
  title: string;
  description: string | null;
  mastery: number;
  confidence: number;
};

export type KnowledgeGraphEdge = {
  source: string;
  target: string;
};

export type KnowledgeGraphResponse = {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
};

export async function getKnowledgeGraph(): Promise<KnowledgeGraphResponse> {
  const response = await fetch(
    `${API_BASE_URL}/twin/knowledge-graph`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch knowledge graph."
    );
  }

  return response.json();
}