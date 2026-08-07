export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`;
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleString();
}

export function statusColor(status: string): "default" | "primary" | "success" | "error" | "warning" {
  switch (status) {
    case "completed":
      return "success";
    case "failed":
      return "error";
    case "running":
      return "primary";
    case "queued":
    case "pending":
      return "warning";
    default:
      return "default";
  }
}

export function truncate(str: string | null | undefined, maxLen = 50): string {
  if (!str) return "";
  return str.length > maxLen ? `${str.slice(0, maxLen)}…` : str;
}
