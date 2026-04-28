import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor to handle 401 errors (expired/invalid cookies)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear local storage and reload to login
      localStorage.removeItem("user");
      // Only redirect if not already on login/register page
      if (!window.location.pathname.match(/^\/(login|register)\/?$/)) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

// Auth endpoints
export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  logout: () => api.post("/auth/logout"),
  getCurrentUser: () => api.get("/auth/me"),
};

// Datasource endpoints
export const datasourceAPI = {
  getAll: () => api.get("/datasources"),
  create: (data) => api.post("/datasources", data),
  delete: (id) => api.delete(`/datasources/${id}`),

  connectSql: (data) => api.post("/datasources/sql/connect", data),
  connectMongo: (data) => api.post("/datasources/mongo/connect", data),
  uploadPandas: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/datasources/pandas/upload", form, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

// AI query endpoints
export const aiAPI = {
  query: (data) => api.post("/ai/query", data),
  getHistory: (datasourceId) =>
    api.get("/ai/history", { params: datasourceId ? { datasource_id: datasourceId } : {} }),
  getSession: (sessionId) => api.get(`/ai/history/${sessionId}`),
  deleteSession: (sessionId) => api.delete(`/ai/history/${sessionId}`),
  autocomplete: (data) => api.post("/ai/autocomplete", data),
  // Visualization endpoints
  suggestVisualizations: (data) => api.post("/ai/visualize/suggest", data),
  generateVisualization: (data) => api.post("/ai/visualize/generate", data),
  // Export endpoints
  exportCSV: (data) =>
    api.post("/ai/export/csv", data, { responseType: "blob" }),
  emailResults: (data) => api.post("/ai/export/email", data),
  // Speech-to-text
  speechToText: (audioBlob) => {
    const form = new FormData();
    form.append("file", audioBlob, "recording.webm");
    return api.post("/ai/speech-to-text", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export default api;

// Helper to turn various API error payloads into readable strings for UI
export function formatApiError(payload) {
  if (!payload) return null;

  // If the backend returns { detail: 'message' }
  const detail = payload.detail ?? payload.error ?? payload.message ?? payload;

  if (typeof detail === "string") return detail;

  // If it's an array of validation errors (pydantic style)
  if (Array.isArray(detail)) {
    try {
      const msgs = detail.map((d) => {
        if (typeof d === "string") return d;
        if (d.msg) return d.msg;
        return JSON.stringify(d);
      });
      return msgs.join(" | ");
    } catch (e) {
      return JSON.stringify(detail);
    }
  }

  // If it's an object with msg/position
  if (typeof detail === "object") {
    if (detail.msg) return detail.msg;
    try {
      return JSON.stringify(detail);
    } catch (e) {
      return String(detail);
    }
  }

  return String(detail);
}
