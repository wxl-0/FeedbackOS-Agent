import "./globals.css";
import { Topbar } from "@/components/layout/topbar";

export const metadata = { title: "FeedBackOS", description: "AI 产品需求发现多智能体平台" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="zh-CN"><body><main className="min-h-screen"><Topbar /><div className="p-4">{children}</div></main></body></html>;
}
