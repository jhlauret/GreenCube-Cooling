import { apiFetch } from './client';

export interface BackendResultComponent {
  component_code: string;
  label: string;
  sensible_w: number;
  latent_w: number;
  total_w: number;
  percentage_of_total: number;
}

export interface BackendResult {
  id: number;
  study_id: number;
  engine: string;
  engine_version: string | null;
  state: 'success' | 'partial' | 'failed' | 'superseded';
  governing_scenario_code: string | null;
  sensible_load_w: number;
  latent_load_w: number;
  total_load_w: number;
  shr: number;
  margin_w: number;
  recommended_capacity_w: number;
  recommended_capacity_kw: number;
  recommended_capacity_btu_h: number;
  commercial_capacity: { id: number; name: string; capacity_btu_h: number; capacity_kw: number } | null;
  confidence_score: number;
  warnings: { code: string; message: string; severity: string }[];
  main_load_drivers: { code: string; label: string; percentage: number }[];
  breakdown: BackendResultComponent[];
  duration_ms: number;
  created_at: string | null;
}

export interface ValidationIssue {
  code: string;
  message: string;
  severity: 'blocking' | 'warning' | 'info';
  blocking: boolean;
  section: string | null;
  field_path: string | null;
}

export interface ValidationReport {
  issues: ValidationIssue[];
  blocking_count: number;
  warning_count: number;
  provenance_summary: Record<string, number>;
  confidence_score: number;
}

export function createStudy(name: string) {
  return apiFetch<{ id: number }>('/studies', { method: 'POST', body: { name } });
}

export function patchStudy(id: number, vals: Record<string, unknown>) {
  return apiFetch(`/studies/${id}`, { method: 'PATCH', body: vals });
}

export function putThermalSpecification(id: number, vals: Record<string, unknown>) {
  return apiFetch(`/studies/${id}/thermal-specification`, { method: 'PUT', body: vals });
}

export function putOccupancyProfile(id: number, vals: Record<string, unknown>) {
  return apiFetch(`/studies/${id}/occupancy-profile`, { method: 'PUT', body: vals });
}

export function putVentilationProfile(id: number, vals: Record<string, unknown>) {
  return apiFetch(`/studies/${id}/ventilation-profile`, { method: 'PUT', body: vals });
}

export function putShading(id: number, entries: Record<string, unknown>[]) {
  return apiFetch(`/studies/${id}/shading`, { method: 'PUT', body: entries as unknown });
}

export interface BackendEquipmentLoad {
  id: number;
  name: string;
  category: string;
  quantity: number;
  unit_power_w: number;
  usage_hours_per_day: number;
  simultaneity_percent: number;
}

export function listEquipmentLoads(id: number) {
  return apiFetch<BackendEquipmentLoad[]>(`/studies/${id}/equipment-loads`);
}

export function createEquipmentLoad(id: number, vals: Record<string, unknown>) {
  return apiFetch<BackendEquipmentLoad>(`/studies/${id}/equipment-loads`, { method: 'POST', body: vals });
}

export function updateEquipmentLoad(lineId: number, vals: Record<string, unknown>) {
  return apiFetch<BackendEquipmentLoad>(`/equipment-loads/${lineId}`, { method: 'PATCH', body: vals });
}

export function deleteEquipmentLoad(lineId: number) {
  return apiFetch(`/equipment-loads/${lineId}`, { method: 'DELETE' });
}

export function getValidation(id: number) {
  return apiFetch<ValidationReport>(`/studies/${id}/validation`);
}

export function confirmAssumptions(id: number) {
  return apiFetch<{ confirmed_count: number }>(`/studies/${id}/assumptions/confirm`, { method: 'POST' });
}

export function calculate(id: number) {
  return apiFetch<BackendResult>(`/studies/${id}/calculations`, { method: 'POST' });
}

export function getStudyResults(id: number) {
  return apiFetch<BackendResult[]>(`/studies/${id}/results`);
}

export interface CatalogProduct {
  id: number;
  name: string;
  type: string | null;
  nominal_capacity_w: number | null;
  capacity_at_35c_w: number | null;
  capacity_at_45c_w: number | null;
  electrical_power_w: number | null;
  eer: number | null;
  seer: number | null;
  shr: number | null;
  noise_db: number | null;
  max_outdoor_temperature_c: number | null;
  power_supply: string | null;
  data_quality: string | null;
  list_price: number | null;
}

export function getEquipmentCatalog() {
  return apiFetch<CatalogProduct[]>('/equipment-catalog');
}

export interface EquipmentRecommendation {
  product: CatalogProduct;
  status: string;
  reasons: string[];
  oversizing_ratio: number | null;
}

export function getEquipmentRecommendations(id: number) {
  return apiFetch<EquipmentRecommendation[]>(`/studies/${id}/equipment-recommendations`, { method: 'POST' });
}

export interface EquipmentSelection {
  id: number;
  product_id: number;
  product_name: string;
  compatibility_status: string;
  state: string;
  result_id: number;
  created_at: string | null;
}

export function listEquipmentSelections(id: number) {
  return apiFetch<EquipmentSelection[]>(`/studies/${id}/equipment-selections`);
}

export function postEquipmentSelection(id: number, productId: number) {
  return apiFetch(`/studies/${id}/equipment-selections`, { method: 'POST', body: { product_id: productId } });
}
