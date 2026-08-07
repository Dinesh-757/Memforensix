import axios, { AxiosInstance } from "axios";

const API_BASE = "/api/v1";

export const apiClient: AxiosInstance = axios.create({ baseURL: API_BASE });

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export interface Analysis {
  id: string;
  filename: string;
  file_size: number;
  file_hash_sha256: string | null;
  dump_format: string;
  status: string;
  progress: number;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ProcessRecord {
  pid: number;
  ppid: number | null;
  name: string;
  create_time: string | null;
  threads: number;
  handles: number;
  cmdline: string | null;
  is_suspicious: boolean;
  suspicion_reasons: string[] | null;
}

export interface NetworkConnection {
  pid: number | null;
  process_name: string | null;
  local_addr: string | null;
  local_port: number | null;
  remote_addr: string | null;
  remote_port: number | null;
  protocol: string | null;
  state: string | null;
  is_suspicious: boolean;
}

export interface YaraMatch {
  rule_name: string;
  rule_namespace: string | null;
  matched_pid: number | null;
  offset: string | null;
  severity: string;
  tags: string[] | null;
  strings_matched: string[] | null;
}

export interface MLFinding {
  entity_type: string;
  entity_ref: string;
  anomaly_score: number;
  is_anomaly: boolean;
  features: Record<string, unknown> | null;
  explanation: string | null;
}

export interface AnalysisResults {
  analysis: Analysis;
  processes: ProcessRecord[];
  connections: NetworkConnection[];
  yara_matches: YaraMatch[];
  ml_findings: MLFinding[];
  summary: Record<string, number>;
}

export const authApi = {
  login: (username: string, password: string) =>
    apiClient.post("/auth/login", { username, password }),
  register: (username: string, email: string, password: string, role = "viewer") =>
    apiClient.post("/auth/register", { username, email, password, role }),
  me: () => apiClient.get("/auth/me"),
};

export const analysisApi = {
  upload: (file: File, onProgress?: (pct: number) => void) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post<Analysis>("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
      },
    });
  },
  list: (page = 1, pageSize = 20) =>
    apiClient.get<{ total: number; items: Analysis[] }>("/analyses", { params: { page, page_size: pageSize } }),
  get: (id: string) => apiClient.get<Analysis>(`/analyses/${id}`),
  delete: (id: string) => apiClient.delete(`/analyses/${id}`),
  results: (id: string) => apiClient.get<AnalysisResults>(`/results/${id}`),
  exportUrl: (id: string, format: "json" | "csv" | "pdf") => `${API_BASE}/results/${id}/export?format=${format}`,
  downloadExport: async (id: string, format: "json" | "csv" | "pdf") => {
    const response = await apiClient.get(`/results/${id}/export`, { params: { format }, responseType: "blob" });
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${id}_report.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
