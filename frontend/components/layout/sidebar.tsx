import type { Chat } from "@/lib/chat/types";

type SidebarProps = {
  chats: Chat[];
  activeChatId: string | null;
  onNewChat: () => void;
  onSelectChat: (chatId: string) => void;
};

export default function Sidebar({
  chats,
  activeChatId,
  onNewChat,
  onSelectChat,
}: SidebarProps) {
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

      {/* Recent Chats */}
      <div className="mt-6 flex-1 overflow-y-auto px-3">
        <p className="px-3 text-xs font-medium uppercase tracking-wider text-zinc-400">
          Recent
        </p>

        <div className="mt-2 space-y-1">
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => onSelectChat(chat.id)}
              className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                chat.id === activeChatId
                  ? "bg-zinc-100 font-medium text-zinc-900"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              {chat.title}
            </button>
          ))}
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="border-t border-zinc-200 p-3">
        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-100">
          <span>🧠</span>
          <span>My Twin</span>
        </button>

        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-100">
          <span>◈</span>
          <span>Knowledge Graph</span>
        </button>

        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-100">
          <span>⚙</span>
          <span>Settings</span>
        </button>
      </div>
    </aside>
  );
}