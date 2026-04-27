import { clsx, type ClassValue } from "clsx";
export function cn(...inputs: ClassValue[]) { return clsx(inputs); }
export function pct(v: number) { return `${Math.round((v || 0) * 100)}%`; }

