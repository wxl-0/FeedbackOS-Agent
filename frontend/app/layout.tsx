import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

export const metadata = { title: "FeedbackOS Agent", description: "AI 产品需求发现多智能体平台" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="zh-CN"><body><Sidebar /><main className="ml-64 min-h-screen"><Topbar /><div className="p-6">{children}</div></main></body></html>;
}

