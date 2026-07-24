import { apiFetch } from './client';

export interface GeoSearchResult {
  label: string;
  city: string | null;
  zip: string | null;
  country_code: string | null;
  latitude: number;
  longitude: number;
  altitude_m: number | null;
  timezone: string | null;
}

export interface GeoContext {
  altitude_m: number | null;
  timezone: string | null;
  utc_offset_seconds: number | null;
}

export function searchAddress(query: string, signal?: AbortSignal): Promise<GeoSearchResult[]> {
  return apiFetch<GeoSearchResult[]>(`/geocode?query=${encodeURIComponent(query)}`, { signal });
}

export function fetchGeoContext(latitude: number, longitude: number, signal?: AbortSignal): Promise<GeoContext> {
  return apiFetch<GeoContext>(`/geo-context?latitude=${latitude}&longitude=${longitude}`, { signal });
}

export interface ConfirmLocationPayload {
  address?: string | null;
  city?: string | null;
  latitude: number;
  longitude: number;
  altitude_m?: number | null;
  timezone?: string | null;
  environment_type?: string | null;
  /** How these coordinates were obtained — never inferred by the backend. */
  provenance: 'manual' | 'geocoded' | 'browser' | 'imported';
  provider?: string | null;
  precision?: 'exact' | 'locality' | 'region' | 'country' | 'unknown';
  /** Minimal, non-PII source snippet kept for audit — see cooling_study.py's
   * action_confirm_geolocation() docstring for exactly what is retained. */
  source?: { display_name?: string; city?: string; country_code?: string; confidence_percent?: number };
}

/**
 * POST /studies/:id/confirm-location (GC-COOLING-03 §16/§17) — the only
 * call that is allowed to set climate_confirmed=true server-side. Must be
 * called before the wizard advances past the location step; a plain PATCH
 * of lat/lon (e.g. autosave of an in-progress edit) never confirms it.
 */
export function confirmLocation(studyId: number, payload: ConfirmLocationPayload) {
  return apiFetch<Record<string, unknown>>(`/studies/${studyId}/confirm-location`, {
    method: 'POST',
    body: payload,
  });
}
