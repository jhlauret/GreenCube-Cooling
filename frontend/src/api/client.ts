/**
 * Thin HTTP client for the greencube_cooling Odoo module's JSON API
 * (addons/greencube_cooling/controllers/api.py). Not yet wired into the
 * store or UI — src/store/studyStore.ts still owns all state via a mocked,
 * localStorage-persisted Zustand store. This module only exposes the
 * building blocks (base URL + fetch wrapper + error shape) needed for that
 * future integration.
 */

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export const API_PREFIX = '/api/v1/greencube/cooling';

/** Mirrors the error envelope returned by every route in controllers/api.py. */
export interface ApiErrorPayload {
  code: string;
  message: string;
  field: string | null;
  section: string | null;
  action: string | null;
  request_id: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly payload: ApiErrorPayload;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

export interface ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

/**
 * Calls `${API_BASE_URL}${API_PREFIX}${path}` and returns the parsed
 * `data` field on success. Odoo session auth relies on the `session_id`
 * cookie, hence `credentials: 'include'` so it is sent on cross-origin
 * requests when the frontend and Odoo are served from different ports.
 */
export async function apiFetch<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
    method: options.method ?? 'GET',
    credentials: 'include',
    headers: {
      ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : undefined),
      ...options.headers,
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  });

  const json = await response.json().catch(() => null);

  if (!response.ok) {
    const payload: ApiErrorPayload = json?.error ?? {
      code: 'UNKNOWN_ERROR',
      message: response.statusText || 'Request failed',
      field: null,
      section: null,
      action: null,
      request_id: 'unknown',
    };
    throw new ApiError(response.status, payload);
  }

  return json?.data as T;
}
