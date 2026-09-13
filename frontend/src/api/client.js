const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL;
const ROOT_BASE_URL = (configuredBaseUrl || "")
  .replace(/\/api\/?$/, "")
  .replace(/\/$/, "")
const API_BASE_URL = configuredBaseUrl
  ? `${ROOT_BASE_URL}/api`
  : "/api"

export async function request(path, options = {}, baseUrl = API_BASE_URL) {
  let response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });
  } catch {
    throw new Error(
      "Backend unavailable. Check that the API server is running.",
    );
  }

  if (!response.ok) {
    let message = `Backend request failed (${response.status})`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // Keep the HTTP error when the server does not return JSON.
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  try {
    return await response.json();
  } catch {
    throw new Error("Backend returned an invalid JSON response.");
  }
}

export const api = {
  getHealth: () => request("/health", {}, ROOT_BASE_URL),
  getDatabaseHealth: () => request("/health/db", {}, ROOT_BASE_URL),
  evaluateDecision: (data) =>
    request("/decision/evaluate", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getProjects: (page = 1, pageSize = 20) =>
    request(`/projects?page=${page}&page_size=${pageSize}`),
  getPortfolioRisk: (page = 1, pageSize = 20) =>
    request(`/risk/portfolio?page=${page}&page_size=${pageSize}`),
  getProject: (projectId) =>
    request(`/projects/${encodeURIComponent(projectId)}`),
  getObservations: (projectId, page = 1, pageSize = 100) =>
    request(
      `/projects/${encodeURIComponent(projectId)}/observations?page=${page}&page_size=${pageSize}`,
    ),
  predict: (projectId, observationId) =>
    request(
      `/projects/${encodeURIComponent(projectId)}/predict?observation_id=${encodeURIComponent(observationId)}`,
      { method: "POST" },
    ),
  getExplanation: (projectId, observationId) =>
    request(
      `/projects/${encodeURIComponent(projectId)}/explanation?observation_id=${encodeURIComponent(observationId)}&top_k=5`,
    ),
  getBacktest: (projectId, observationId) =>
    request(
      `/projects/${encodeURIComponent(projectId)}/backtest?observation_id=${encodeURIComponent(observationId)}`,
    ),
  getTrajectory: (projectId) =>
    request(`/projects/${encodeURIComponent(projectId)}/risk-trajectory`),
  getIntelligence: (projectId, observationId, query) =>
    request(
      `/intelligence/projects/${encodeURIComponent(projectId)}/observations/${encodeURIComponent(observationId)}`,
      {
        method: "POST",
        body: JSON.stringify({ query }),
      },
    ),
};
