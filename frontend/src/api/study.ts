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
  id: string;
  code: string;
  title: string;
  message: string;
  // Matches cooling_study.py's get_validation()/add_issue() exactly:
  // 'error'|'warning'|'info', not 'blocking' — `blocking` is its own
  // separate boolean field (audit P2-08: these two were out of sync).
  severity: 'error' | 'warning' | 'info';
  blocking: boolean;
  section_code: string | null;
  field_path: string | null;
}

export interface ValidationReport {
  issues: ValidationIssue[];
  blocking_count: number;
  warning_count: number;
  info_count: number;
  ready: boolean;
  provenance_summary: Record<string, number>;
  /** Completeness/provenance quality, computable before any solver run. */
  completeness_score: number;
  /** Solver output — stays 0 until a calculation has actually run. */
  confidence_score: number;
}

export interface BackendStudySummary {
  id: number;
  reference: string | null;
  name: string;
  state: string;
  revision_number: number;
  parent_study_id: number | null;
  root_study_id: number | null;
  location: { address: string | null; city: string | null };
  confidence_score: number;
  active_result_id: number | null;
  updated_at: string | null;
}

export function listStudies() {
  return apiFetch<BackendStudySummary[]>('/studies');
}

export function createStudy(name: string) {
  return apiFetch<{ id: number }>('/studies', { method: 'POST', body: { name } });
}

export function getStudy(id: number) {
  return apiFetch<BackendStudySummary & Record<string, unknown>>(`/studies/${id}`);
}

export function patchStudy(id: number, vals: Record<string, unknown>) {
  return apiFetch(`/studies/${id}`, { method: 'PATCH', body: vals });
}

/** Locks the study (state -> validated); requires state=calculated first. */
export function validateStudy(id: number) {
  return apiFetch<BackendStudySummary>(`/studies/${id}/validate`, { method: 'POST' });
}

/** Creates a new draft revision of a validated (locked) study, copying its
 * sub-lines. Returns the new revision's id — the caller should switch the
 * local draft to track it, not the original. */
export function createRevision(id: number) {
  return apiFetch<BackendStudySummary>(`/studies/${id}/revisions`, { method: 'POST' });
}

export interface BackendFacade {
  id: number;
  orientation: string;
  gross_area_m2: number;
  glazing_area_m2: number;
}

export interface BackendThermalSpecification {
  id: number;
  code: string;
  version: string;
  standard_model: boolean;
  source_template_id: number | null;
  source_template_version: string | null;
  length_m: number;
  width_m: number;
  height_m: number;
  wall_u_value: number;
  roof_u_value: number;
  floor_u_value: number;
  airtightness_n50: number;
  thermal_mass_level: string;
  notes: string | false;
  facades: BackendFacade[];
}

export function getThermalSpecification(id: number) {
  return apiFetch<BackendThermalSpecification | null>(`/studies/${id}/thermal-specification`);
}

export function putThermalSpecification(id: number, vals: Record<string, unknown>) {
  return apiFetch(`/studies/${id}/thermal-specification`, { method: 'PUT', body: vals });
}

/** The canonical GreenCube model catalog (GC-COOLING-08) — never hardcode these client-side. */
export function getThermalSpecificationTemplates() {
  return apiFetch<BackendThermalSpecification[]>('/thermal-specification-templates');
}

export interface BackendOccupancyProfile {
  id: number;
  usage_type: string;
  usual_occupants: number;
  maximum_occupants: number;
  activity_level: string;
  usage_days: string;
  start_hour: number;
  end_hour: number;
  used_at_night: boolean;
}

export function getOccupancyProfile(id: number) {
  return apiFetch<BackendOccupancyProfile | null>(`/studies/${id}/occupancy-profile`);
}

export function putOccupancyProfile(id: number, vals: Record<string, unknown>) {
  return apiFetch(`/studies/${id}/occupancy-profile`, { method: 'PUT', body: vals });
}

export interface BackendVentilationProfile {
  id: number;
  ventilation_type: string;
  airflow_m3h: number;
}

export function getVentilationProfile(id: number) {
  return apiFetch<BackendVentilationProfile | null>(`/studies/${id}/ventilation-profile`);
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

export interface CalculationJob {
  job_id: number;
  status: string;
  result_id: number;
  engine: string;
  engine_version: string | null;
  request_id: string;
}

/**
 * Triggers a calculation. Odoo runs MERCURE synchronously today, but the
 * response is a job envelope (not a result) so the contract already
 * supports a future asynchronous EnergyPlus job without another breaking
 * change. Callers must follow up with getResult(job.result_id).
 */
export function calculate(id: number, idempotencyKey?: string) {
  return apiFetch<CalculationJob>(`/studies/${id}/calculations`, {
    method: 'POST',
    headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined,
  });
}

export function getCalculationJob(jobId: number) {
  return apiFetch<CalculationJob>(`/calculations/${jobId}`);
}

export function getResult(resultId: number) {
  return apiFetch<BackendResult>(`/results/${resultId}`);
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
  /** Frozen at selection time — not a live lookup, so a later catalog
   * rename/respec doesn't silently rewrite this selection's history. */
  product_name: string;
  capacity_at_45c_w: number;
  max_outdoor_temperature_c: number;
  shr: number;
  eer: number;
  nominal_capacity_w: number;
  price: number;
  currency: string | null;
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
