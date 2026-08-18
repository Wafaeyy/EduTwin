export default function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-zinc-200 px-6">
      <div>
        <h1 className="text-sm font-medium text-zinc-500">
          AI Learning Companion
        </h1>
      </div>

      <button className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-100 text-sm font-medium text-zinc-700 transition hover:bg-zinc-200">
        Y
      </button>
    </header>
  );
}