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