"use client";

import { useEffect, useRef, useState } from "react";

import Message from "./message";

import { sendChatMessage } from "@/lib/api/chat";

import type { Chat } from "@/lib/chat/types";

type ChatWindowProps = {
  chat: Chat;
  onUpdateChat: (chat: Chat) => void;
};

export default function ChatWindow({
  chat,
  onUpdateChat,
}: ChatWindowProps) {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef =
    useRef<HTMLDivElement | null>(null);

  /*
   * Automatically scroll to the newest message.
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [chat.messages, isLoading]);

  async function handleSend() {
    const trimmedInput = input.trim();

    if (!trimmedInput || isLoading) {
      return;
    }

    setError(null);

    const userMessage = {
      id: Date.now(),
      role: "user" as const,
      content: trimmedInput,
    };

    /*
     * Add the user's message immediately.
     */
    const updatedMessages = [
      ...chat.messages,
      userMessage,
    ];

    /*
     * Automatically use the first user message
     * as the conversation title.
     */
    const newTitle =
      chat.messages.length === 0
        ? trimmedInput.slice(0, 40)
        : chat.title;

    const updatedChat: Chat = {
      ...chat,
      title: newTitle,
      messages: updatedMessages,
      updatedAt: Date.now(),
    };

    onUpdateChat(updatedChat);

    setInput("");
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        message: trimmedInput,
      });

      const assistantMessage = {
        id: Date.now(),
        role: "assistant" as const,
        content: response.answer,
      };

      const finalChat: Chat = {
        ...updatedChat,
        messages: [
          ...updatedMessages,
          assistantMessage,
        ],
        updatedAt: Date.now(),
      };

      onUpdateChat(finalChat);
    } catch (error) {
      console.error(
        "Chat request failed:",
        error
      );

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
          {chat.messages.length === 0 && (
            <div className="mb-4 text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-900 text-sm font-semibold text-white">
                E
              </div>

              <h2 className="mt-4 text-xl font-semibold text-zinc-900">
                How can I help you learn?
              </h2>

              <p className="mt-1 text-sm text-zinc-500">
                Ask me anything about your studies,
                skills, or career.
              </p>
            </div>
          )}

          {/* Messages */}
          {chat.messages.map((message) => (
            <Message
              key={message.id}
              role={message.role}
              content={message.content}
            />
          ))}

          {/* Loading */}
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
              onChange={(event) =>
                setInput(event.target.value)
              }
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
              disabled={
                isLoading || !input.trim()
              }
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-sm text-white transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              ↑
            </button>
          </div>

          <p className="mt-2 text-center text-xs text-zinc-400">
            EduTwin uses your learning context to
            personalize responses.
          </p>
        </div>
      </div>
    </div>
  );
}