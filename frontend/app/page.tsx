/*TO RUN
cd D:\EduTwin\frontend
npm run dev
*/
import Sidebar from "@/components/layout/sidebar";
import Header from "@/components/layout/header";
import ChatWindow from "@/components/chat/chat_window";

export default function Home() {
  return (
    <div className="flex h-screen bg-zinc-50">
      <Sidebar />

      <main className="flex min-w-0 flex-1 flex-col">
        <Header />
        <ChatWindow />
      </main>
    </div>
  );
}