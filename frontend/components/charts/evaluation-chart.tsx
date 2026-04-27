"use client";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
export function EvaluationChart({ data }: { data: any[] }) {
  return <ResponsiveContainer width="100%" height={180}><BarChart data={data}><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="value" fill="#216869" radius={[4,4,0,0]} /></BarChart></ResponsiveContainer>;
}

