import { useAuthStore } from "@/stores/auth-store";
import type { TokenPair } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

let refreshPromise: Promise<boolean> | null = null;

function normalizeDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "object" && item !== null) {
          const record = item as { msg?: unknown; loc?: unknown };
          const msg = typeof record.msg === "string" ? record.msg : "Invalid value";
          const loc = Array.isArray(record.loc)
            ? record.loc.filter((p) => typeof p === "string").join(".")
            : "";
          return loc ? `${loc}: ${msg}` : msg;
        }
        return String(item);
      })
      .join("; ");
  }
  if (detail === null || detail === undefined) return "Request failed";
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail);
  }
}

async function refreshTokens(): Promise<boolean> {
  const { refreshToken } = useAuthStore.getState();
  if (!refreshToken) return false;

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) {
          useAuthStore.getState().clear();
          return false;
        }
        const pair = (await res.json()) as TokenPair;
        useAuthStore.getState().setTokens(pair);
        return true;
      } catch {
        useAuthStore.getState().clear();
        return false;
      } finally {
        refreshPromise = null;
      }
    })();
  }

  return refreshPromise;
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean;
  retryOn401?: boolean;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const {
    body,
    auth = true,
    retryOn401 = true,
    headers,
    ...rest
  } = options;

  const token = useAuthStore.getState().accessToken;
  const finalHeaders = new Headers(headers);
  if (body !== undefined) {
    finalHeaders.set("Content-Type", "application/json");
  }
  if (auth && token) {
    finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1${path}`, {
      ...rest,
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Cannot reach the API server");
  }

  if (res.status === 401 && auth && retryOn401) {
    const refreshed = await refreshTokens();
    if (!refreshed) {
      useAuthStore.getState().clear();
      throw new ApiError(401, "Session expired. Please sign in again.");
    }
    return apiFetch<T>(path, { ...options, retryOn401: false });
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!res.ok) {
    const detail =
      payload !== null &&
      typeof payload === "object" &&
      "detail" in payload
        ? normalizeDetail((payload as { detail: unknown }).detail)
        : `Request failed with status ${res.status}`;
    throw new ApiError(res.status, detail);
  }

  return payload as T;
}
