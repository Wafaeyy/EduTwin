"use client";

import { useEffect, useRef, useState } from "react";
import Message from "./message";
import { sendChatMessage } from "@/lib/api/chat";

type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

const initialMessages: ChatMessage[] = [
  {
    id: 1,
    role: "user",
    content: "Explain neural networks to me.",
  },
  {
    id: 2,
    role: "assistant",
    content:
      "Sure! A neural network is a machine learning model inspired by the way biological neurons process information. Let's break it down step by step.",
  },
];

export default function ChatWindow() {
  const [messages, setMessages] =
    useState<ChatMessage[]>(initialMessages);

  const [input, setInput] = useState("");

  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
  messagesEndRef.current?.scrollIntoView({
    behavior: "smooth",
  });
}, [messages, isLoading]);

  async function handleSend() {
    const trimmedInput = input.trim();

    if (!trimmedInput || isLoading) {
      return;
    }

    setError(null);

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: trimmedInput,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);

    setInput("");
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        message: trimmedInput,
      });

      const assistantMessage: ChatMessage = {
        id: Date.now(),
        role: "assistant",
        content: response.answer,
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);
    } catch (error) {
      console.error("Chat request failed:", error);

      setError(
        "Something went wrong while contacting EduTwin. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Conversation */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-6">
          {/* Welcome */}
          <div className="mb-4 text-center">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-900 text-sm font-semibold text-white">
              E
            </div>

            <h2 className="mt-4 text-xl font-semibold text-zinc-900">
              How can I help you learn?
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              Ask me anything about your studies, skills, or career.
            </p>
          </div>

          {/* Messages */}
          {messages.map((message) => (
            <Message
              key={message.id}
              role={message.role}
              content={message.content}
            />
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-2xl bg-white px-4 py-3 text-sm text-zinc-500 shadow-sm ring-1 ring-zinc-200">
                EduTwin is thinking...
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}
          {/* for scroll down effect add bottom marker */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-zinc-200 bg-zinc-50 px-6 py-4">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-center gap-3 rounded-2xl border border-zinc-200 bg-white px-4 py-3 shadow-sm">
            <input
              type="text"
              value={input}
              disabled={isLoading}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSend();
                }
              }}
              placeholder={
                isLoading
                  ? "EduTwin is thinking..."
                  : "Ask EduTwin anything..."
              }
              className="flex-1 bg-transparent text-sm text-zinc-800 outline-none placeholder:text-zinc-400 disabled:cursor-not-allowed"
            />

            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-sm text-white transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              ↑
            </button>
          </div>

          <p className="mt-2 text-center text-xs text-zinc-400">
            EduTwin uses your learning context to personalize responses.
          </p>
        </div>
      </div>
    </div>
  );
}