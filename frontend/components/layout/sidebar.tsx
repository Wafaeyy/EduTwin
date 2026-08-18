export default function Sidebar() {
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
        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100">
          <span className="text-lg">+</span>
          <span>New chat</span>
        </button>
      </div>

      {/* Recent Chats */}
      <div className="mt-6 flex-1 px-3">
        <p className="px-3 text-xs font-medium uppercase tracking-wider text-zinc-400">
          Recent
        </p>

        <div className="mt-2 space-y-1">
          <button className="w-full truncate rounded-lg px-3 py-2 text-left text-sm text-zinc-600 transition hover:bg-zinc-100">
            Python learning plan
          </button>

          <button className="w-full truncate rounded-lg px-3 py-2 text-left text-sm text-zinc-600 transition hover:bg-zinc-100">
            Machine learning roadmap
          </button>

          <button className="w-full truncate rounded-lg px-3 py-2 text-left text-sm text-zinc-600 transition hover:bg-zinc-100">
            Career advice
          </button>
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
          <span>Knowledge</span>
        </button>

        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-700 transition hover:bg-zinc-100">
          <span>⚙</span>
          <span>Settings</span>
        </button>
      </div>
    </aside>
  );
}