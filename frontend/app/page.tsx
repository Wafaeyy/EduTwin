"use client";

import { useEffect, useState } from "react";

import Sidebar from "@/components/layout/sidebar";
import Header from "@/components/layout/header";
import ChatWindow from "@/components/chat/chat_window";

import type { Chat } from "@/lib/chat/types";
import {
  createChat,
  loadChats,
  saveChats,
} from "@/lib/chat/storage";

export default function Home() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(
    null
  );

  /*
   * Load saved chats when the application starts.
   */
  useEffect(() => {
    const storedChats = loadChats();

    if (storedChats.length > 0) {
      setChats(storedChats);
      setActiveChatId(storedChats[0].id);
    } else {
      const newChat = createChat();

      setChats([newChat]);
      setActiveChatId(newChat.id);

      saveChats([newChat]);
    }
  }, []);

  /*
   * Save chats whenever they change.
   */
  useEffect(() => {
    if (chats.length > 0) {
      saveChats(chats);
    }
  }, [chats]);

  /*
   * Create a new conversation.
   *
   * If the current conversation is already empty,
   * don't create another empty conversation.
   */
  function handleNewChat() {
    const activeChat = chats.find(
      (chat) => chat.id === activeChatId
    );

    if (
      activeChat &&
      activeChat.messages.length === 0
    ) {
      return;
    }

    const newChat = createChat();

    setChats((currentChats) => [
      newChat,
      ...currentChats,
    ]);

    setActiveChatId(newChat.id);
  }

  /*
   * Delete a conversation.
   *
   * If the deleted conversation is active,
   * another conversation becomes active.
   *
   * If it was the only conversation,
   * create a fresh empty conversation.
   */
  function handleDeleteChat(chatId: string) {
    const chatIndex = chats.findIndex(
      (chat) => chat.id === chatId
    );

    if (chatIndex === -1) {
      return;
    }

    const remainingChats = chats.filter(
      (chat) => chat.id !== chatId
    );

    /*
     * If the user deleted the only conversation,
     * create a fresh empty conversation.
     */
    if (remainingChats.length === 0) {
      const newChat = createChat();

      setChats([newChat]);
      setActiveChatId(newChat.id);

      return;
    }

    setChats(remainingChats);

    /*
     * If the deleted conversation was active,
     * select another conversation.
     */
    if (chatId === activeChatId) {
      const nextChat =
        remainingChats[chatIndex] ??
        remainingChats[chatIndex - 1] ??
        remainingChats[0];

      setActiveChatId(nextChat.id);
    }
  }

  /*
   * Rename a conversation.
   */
  function handleRenameChat(
    chatId: string,
    newTitle: string
  ) {
    const trimmedTitle = newTitle.trim();

    if (!trimmedTitle) {
      return;
    }

    setChats((currentChats) =>
      currentChats.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              title: trimmedTitle,
              updatedAt: Date.now(),
            }
          : chat
      )
    );
  }

  /*
   * Find the currently active conversation.
   */
  const activeChat = chats.find(
    (chat) => chat.id === activeChatId
  );

  return (
    <div className="flex h-screen bg-zinc-50">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onNewChat={handleNewChat}
        onSelectChat={setActiveChatId}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChat}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <Header />

        {activeChat && (
          <ChatWindow
            chat={activeChat}
            onUpdateChat={(updatedChat) => {
              setChats((currentChats) =>
                currentChats.map((chat) =>
                  chat.id === updatedChat.id
                    ? updatedChat
                    : chat
                )
              );
            }}
          />
        )}
      </main>
    </div>
  );
}