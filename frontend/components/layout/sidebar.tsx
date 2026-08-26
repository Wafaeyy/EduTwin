"use client";

import { useState } from "react";

import Link from "next/link";

import type { Chat } from "@/lib/chat/types";

type SidebarProps = {
  chats: Chat[];
  activeChatId: string | null;
  onNewChat: () => void;
  onSelectChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
  onRenameChat: (chatId: string, newTitle: string) => void;
};

type ChatGroup = {
  title: string;
  chats: Chat[];
};

export default function Sidebar({
  chats,
  activeChatId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onRenameChat,
}: SidebarProps) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(
    null
  );

  const [renamingChatId, setRenamingChatId] = useState<
    string | null
  >(null);

  const [renameValue, setRenameValue] = useState("");

  /*
   * Start renaming a conversation.
   */
  function startRename(chat: Chat) {
    setRenamingChatId(chat.id);
    setRenameValue(chat.title);
    setOpenMenuId(null);
  }

  /*
   * Finish renaming a conversation.
   */
  function finishRename(chatId: string) {
    const trimmedValue = renameValue.trim();

    if (trimmedValue) {
      onRenameChat(chatId, trimmedValue);
    }

    setRenamingChatId(null);
    setRenameValue("");
  }

  /*
   * Format the time shown beside a chat.
   */
  function formatChatTime(timestamp: number) {
    const date = new Date(timestamp);
    const now = new Date();

    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
      });
    }

    return date.toLocaleDateString([], {
      month: "short",
      day: "numeric",
    });
  }

  /*
   * Group chats based on when they were last updated.
   */
  function groupChats(chats: Chat[]): ChatGroup[] {
    const now = new Date();

    const startOfToday = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate()
    );

    const startOfYesterday = new Date(
      startOfToday
    );

    startOfYesterday.setDate(
      startOfYesterday.getDate() - 1
    );

    const startOfSevenDaysAgo = new Date(
      startOfToday
    );

    startOfSevenDaysAgo.setDate(
      startOfSevenDaysAgo.getDate() - 7
    );

    const today: Chat[] = [];
    const yesterday: Chat[] = [];
    const previousSevenDays: Chat[] = [];
    const older: Chat[] = [];

    chats.forEach((chat) => {
      const chatDate = new Date(chat.updatedAt);

      if (chatDate >= startOfToday) {
        today.push(chat);
      } else if (chatDate >= startOfYesterday) {
        yesterday.push(chat);
      } else if (chatDate >= startOfSevenDaysAgo) {
        previousSevenDays.push(chat);
      } else {
        older.push(chat);
      }
    });

    return [
      {
        title: "Today",
        chats: today,
      },
      {
        title: "Yesterday",
        chats: yesterday,
      },
      {
        title: "Previous 7 days",
        chats: previousSevenDays,
      },
      {
        title: "Older",
        chats: older,
      },
    ].filter((group) => group.chats.length > 0);
  }

  /*
   * Always show the most recently updated
   * conversations first.
   */
  const sortedChats = [...chats].sort(
    (a, b) => b.updatedAt - a.updatedAt
  );

  const chatGroups = groupChats(sortedChats);

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-zinc-200 bg-white">
      {/* Logo */}
      <div className="flex h-16 items-center px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-sm font-semibold text-white">
            E
          </div>

          <span className="text-lg font-semibold tracking-tight text-zinc-900">
            EduTwin
          </span>
        </div>
      </div>

      {/* New Chat */}
      <div className="px-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100"
        >
          <span className="text-lg">+</span>
          <span>New chat</span>
        </button>
      </div>

      {/* Conversations */}
      <div className="mt-6 flex-1 overflow-y-auto px-3">
        {chatGroups.map((group) => (
          <div key={group.title} className="mb-6">
            {/* Group title */}
            <p className="px-3 text-xs font-medium uppercase tracking-wider text-zinc-400">
              {group.title}
            </p>

            <div className="mt-2 space-y-1">
              {group.chats.map((chat) => {
                const isActive =
                  chat.id === activeChatId;

                const isMenuOpen =
                  chat.id === openMenuId;

                const isRenaming =
                  chat.id === renamingChatId;

                return (
                  <div
                    key={chat.id}
                    className={`group relative flex items-center rounded-lg transition ${
                      isActive
                        ? "bg-zinc-100"
                        : "hover:bg-zinc-100"
                    }`}
                  >
                    {/* Chat title / Rename input */}
                    {isRenaming ? (
                      <input
                        autoFocus
                        value={renameValue}
                        onChange={(event) =>
                          setRenameValue(
                            event.target.value
                          )
                        }
                        onBlur={() =>
                          finishRename(chat.id)
                        }
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            finishRename(chat.id);
                          }

                          if (event.key === "Escape") {
                            setRenamingChatId(null);
                            setRenameValue("");
                          }
                        }}
                        className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-zinc-900 outline-none"
                      />
                    ) : (
                      <button
                        onClick={() =>
                          onSelectChat(chat.id)
                        }
                        className="min-w-0 flex-1 px-3 py-2 text-left"
                      >
                        <div
                          className={`truncate text-sm ${
                            isActive
                              ? "font-medium text-zinc-900"
                              : "text-zinc-600"
                          }`}
                        >
                          {chat.title}
                        </div>

                        <div className="mt-0.5 text-[11px] text-zinc-400">
                          {formatChatTime(
                            chat.updatedAt
                          )}
                        </div>
                      </button>
                    )}

                    {/* Three-dot menu */}
                    {!isRenaming && (
                      <button
                        onClick={(event) => {
                          event.stopPropagation();

                          setOpenMenuId(
                            isMenuOpen
                              ? null
                              : chat.id
                          );
                        }}
                        aria-label={`Options for ${chat.title}`}
                        title="Chat options"
                        className={`mr-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-zinc-400 transition hover:bg-zinc-200 hover:text-zinc-700 ${
                          isMenuOpen
                            ? "opacity-100"
                            : "opacity-0 group-hover:opacity-100"
                        }`}
                      >
                        <span className="text-lg leading-none">
                          ⋯
                        </span>
                      </button>
                    )}

                    {/* Chat options menu */}
                    {isMenuOpen && (
                      <div className="absolute right-1 top-10 z-20 w-36 rounded-lg border border-zinc-200 bg-white p-1 shadow-lg">
                        <button
                          onClick={() =>
                            startRename(chat)
                          }
                          className="flex w-full items-center rounded-md px-3 py-2 text-left text-sm text-zinc-700 transition hover:bg-zinc-100"
                        >
                          Rename
                        </button>

                        <button
                          onClick={() => {
                            setOpenMenuId(null);
                            onDeleteChat(chat.id);
                          }}
                          className="flex w-full items-center rounded-md px-3 py-2 text-left text-sm text-red-600 transition hover:bg-red-50"
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Bottom Navigation */}
      <div className="border-t border-zinc-200 p-3">
        <Link
        href="/twin"
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-100"
        >
        <span>🧠</span>
        <span>My Twin</span>
</Link>

        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-100">
          <span>◈</span>
          <span>Knowledge Graph</span>
        </button>

        <Link
        href="/settings"
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-100"
        >
        <span>⚙</span>
        <span>Settings</span>
        </Link>
      </div>
    </aside>
  );
}