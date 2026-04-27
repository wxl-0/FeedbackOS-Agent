"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bot, Brain, FileText, Inbox, LayoutDashboard, Lightbulb, Network, UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  ["Dashboard", "/dashboard", LayoutDashboard],
  ["Upload Center", "/upload", UploadCloud],
  ["Feedback Inbox", "/feedback", Inbox],
  ["Insight Clusters", "/clusters", Network],
  ["Opportunity Board", "/opportunities", Lightbulb],
  ["Agent Console", "/agent-console", Bot],
  ["PRD Studio", "/prd-studio", FileText],
  ["Memory Center", "/memory", Brain],
  ["Evaluation", "/evaluation", BarChart3]
] as const;

export function Sidebar() {
  const path = usePathname();
  return <aside className="fixed inset-y-0 left-0 z-10 w-64 border-r border-line bg-white">
    <div className="flex h-16 items-center border-b border-line px-5">
      <div>
        <div className="text-sm font-semibold tracking-wide text-brand">FeedbackOS Agent</div>
        <div className="text-xs text-muted">AI 产品需求发现平台</div>
      </div>
    </div>
    <nav className="space-y-1 p-3">
      {items.map(([label, href, Icon]) => <Link key={href} href={href} className={cn("flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted hover:bg-slate-50 hover:text-ink", path === href && "bg-[#e9f3f2] text-brand")}>
        <Icon size={17} /> {label}
      </Link>)}
    </nav>
  </aside>;
}

