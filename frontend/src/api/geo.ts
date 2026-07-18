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
