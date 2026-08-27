import type { Chat } from "./types";

const STORAGE_KEY = "edutwin-chats";

export function createChat(): Chat {
  const now = Date.now();

  return {
    id: `chat-${now}`,
    title: "New conversation",
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
}

export function loadChats(): Chat[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return [];
    }

    return JSON.parse(stored) as Chat[];
  } catch (error) {
    console.error("Failed to load chats:", error);
    return [];
  }
}

export function saveChats(chats: Chat[]): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(chats)
    );
  } catch (error) {
    console.error("Failed to save chats:", error);
  }
}

export function deleteChat(chatId: string): void {
  const chats = loadChats();

  const updatedChats = chats.filter(
    (chat) => chat.id !== chatId
  );

  saveChats(updatedChats);
}

export function updateChat(updatedChat: Chat): void {
  const chats = loadChats();

  const updatedChats = chats.map((chat) =>
    chat.id === updatedChat.id
      ? updatedChat
      : chat
  );

  saveChats(updatedChats);
}