const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const token = localStorage.getItem("scm-token");
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers,
    signal,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(message || `Request failed for ${path}`, response.status);
  }

  return (await response.json()) as T;
}

export async function apiPost<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  signal?: AbortSignal,
): Promise<TResponse> {
  const token = localStorage.getItem("scm-token");
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(message || `Request failed for ${path}`, response.status);
  }

  return (await response.json()) as TResponse;
}

export async function apiPut<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  signal?: AbortSignal,
): Promise<TResponse> {
  const token = localStorage.getItem("scm-token");
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(message || `Request failed for ${path}`, response.status);
  }

  return (await response.json()) as TResponse;
}

export async function apiDelete<TResponse>(path: string, signal?: AbortSignal): Promise<TResponse> {
  const token = localStorage.getItem("scm-token");
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
    headers,
    signal,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(message || `Request failed for ${path}`, response.status);
  }

  return (await response.json()) as TResponse;
}

export async function apiDownload(path: string, signal?: AbortSignal): Promise<{ blob: Blob; filename?: string }> {
  const token = localStorage.getItem("scm-token");
  const headers: Record<string, string> = {
    Accept: "application/pdf,application/octet-stream",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers,
    signal,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(message || `Request failed for ${path}`, response.status);
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/i);

  return {
    blob: await response.blob(),
    filename: filenameMatch?.[1],
  };
}

export { API_BASE_URL };

// anything
