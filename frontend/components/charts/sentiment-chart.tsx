"use client";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
const colors = ["#216869", "#d77a61", "#7a89a6", "#e6b85c"];
export function SentimentChart({ data }: { data: any[] }) {
  return <ResponsiveContainer width="100%" height={220}><PieChart><Pie dataKey="value" data={data} innerRadius={55} outerRadius={84}>{data?.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer>;
}

