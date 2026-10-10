const DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1";

// VITE_API_URL is baked in at build time by the frontend Dockerfile.
// Local development falls back to the default backend address.
export const API_URL = import.meta.env.VITE_API_URL ?? DEFAULT_API_URL;

// localStorage key that holds the JWT.
const TOKEN_KEY = "token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return String(error);
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);

  // Login sends a form body because FastAPI's OAuth2 flow expects form fields.
  // Every other endpoint sends JSON.
  const isFormBody = options.body instanceof URLSearchParams;

  if (!isFormBody) {
    headers.set("Content-Type", "application/json");
  }

  const token = getToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText;

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (body.detail) {
        detail = JSON.stringify(body.detail);
      }
    } catch {
      // The error body was not JSON.
    }

    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return (await response.json()) as T;
}