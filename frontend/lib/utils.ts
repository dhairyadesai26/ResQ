import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatUptime(seconds: number): string {
  if (!seconds || seconds <= 0) return "0s";
  const sec = Math.floor(seconds);
  const hrs = Math.floor(sec / 3600);
  const mins = Math.floor((sec % 3600) / 60);
  const s = sec % 60;

  if (hrs > 0) return `${hrs}h ${mins}m ${s}s`;
  if (mins > 0) return `${mins}m ${s}s`;
  return `${s}s`;
}

export function formatBytes(bytes: number): string {
  if (!bytes || bytes <= 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Parses any ISO timestamp and ensures it is evaluated with UTC offset if naive,
 * then converts to Indian Standard Time (IST - Asia/Kolkata).
 */
function parseToDate(dateString: string): Date {
  if (!dateString) return new Date();
  let str = dateString.trim();
  // If no timezone suffix like 'Z' or '+05:30' exists, assume UTC
  if (!str.endsWith("Z") && !/[+-]\d{2}(:\d{2})?$/.test(str)) {
    str += "Z";
  }
  return new Date(str);
}

/**
 * Formats a timestamp into Real Indian Standard Time (IST): e.g. "11:45:09 AM IST"
 */
export function formatIndianTime(dateString: string, includeZone = true): string {
  if (!dateString) return "—";
  try {
    const d = parseToDate(dateString);
    if (isNaN(d.getTime())) return dateString;
    const timeStr = d.toLocaleTimeString("en-IN", {
      timeZone: "Asia/Kolkata",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    }).toUpperCase();
    return includeZone ? `${timeStr} IST` : timeStr;
  } catch {
    return dateString;
  }
}

/**
 * Formats a timestamp into Real Indian Date & Time (IST): e.g. "11 Nov, 11:45:09 AM IST"
 */
export function formatIndianDateTime(dateString: string): string {
  if (!dateString) return "—";
  try {
    const d = parseToDate(dateString);
    if (isNaN(d.getTime())) return dateString;
    const datePart = d.toLocaleDateString("en-IN", {
      timeZone: "Asia/Kolkata",
      day: "2-digit",
      month: "short",
    });
    const timePart = d.toLocaleTimeString("en-IN", {
      timeZone: "Asia/Kolkata",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    }).toUpperCase();
    return `${datePart}, ${timePart} IST`;
  } catch {
    return dateString;
  }
}

/**
 * Universal formatter defaulting to Real Indian Standard Time (IST).
 */
export function formatDate(dateString: string): string {
  return formatIndianTime(dateString, true);
}
