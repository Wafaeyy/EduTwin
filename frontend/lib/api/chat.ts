export type ChatRequest = {
  message: string;
};

export type ChatResponse = {
  answer: string;
};

const API_BASE_URL = "http://127.0.0.1:8000";

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(
      `EduTwin API request failed: ${response.status}`
    );
  }

  return response.json();
}