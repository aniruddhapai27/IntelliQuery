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
};

// AI query endpoints
export const aiAPI = {
  query: (data) => api.post("/ai/query", data),
  getHistory: () => api.get("/ai/history"),
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
