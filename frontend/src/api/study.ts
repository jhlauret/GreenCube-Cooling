import { apiFetch } from './client';

export interface BackendResultComponent {
  component_code: string;
  label: string;
  sensible_w: number;
  latent_w: number;
  total_w: number;
  percentage_of_total: number;
}

/** Per-facade share of `breakdown`'s single "solar_glazing" total —
 * informative decomposition only, never additional load on top of it
 * (GC-COOLING-09 pt.11). */
export interface BackendFacadeSolarGain {
  facade: 'north' | 'south' | 'east' | 'west';
  area_m2: number;
  radiation_wm2: number;
  solar_factor: number;
  protection_factor: number;
  gain_w: number;
}

export interface BackendResult {
  id: number;
  study_id: number;
  job_id: number | null;
  engine: string;
  engine_version: string | null;
  requested_engine: 'quick_solver' | 'energyplus' | 'both' | null;
  energyplus_processing_status:
    | 'not_requested'
    | 'disabled'
    | 'translation_failed'
    | 'queued_for_worker'
    | 'simulation_running'
    | 'simulation_unavailable'
    | 'simulation_failed'
    | 'simulation_completed';
  /** True only for the study's single latest successful result — never
   * inferred client-side, always the backend's own answer (GC-COOLING-16). */
  is_current: boolean;
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
  solar_gain_by_facade: BackendFacadeSolarGain[];
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

/**
 * `ifMatch` carries the backend `updated_at` this draft was last synced
 * against (StudyDraft.backendUpdatedAt). The controller compares it to the
 * study's current `write_date` and returns 409 COOLING_STUDY_VERSION_CONFLICT
 * if someone else (another tab, another user) wrote to the study meanwhile —
 * this is what makes autosave's optimistic-locking real instead of a client
 * field nobody sends (GC-COOLING-06 §17 "verrouillage optimiste").
 */
export function patchStudy(id: number, vals: Record<string, unknown>, ifMatch?: string | null) {
  return apiFetch<BackendStudySummary & Record<string, unknown>>(`/studies/${id}`, {
    method: 'PATCH',
    body: vals,
    headers: ifMatch ? { 'If-Match': ifMatch } : undefined,
  });
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

/** GC-COOLING-13: re-runs the backend's structured validation
 * (get_validation()'s blocking rules) and, only if there are no blocking
 * issues, transitions the study to `ready`. The frontend must never flip
 * this state locally from its own client-side checks — a 422
 * STUDY_INCOMPLETE response here means the backend disagrees with
 * whatever the review screen believed was true. */
export function markStudyReady(id: number) {
  return apiFetch<BackendStudySummary>(`/studies/${id}/ready`, { method: 'POST' });
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
  /** Legacy display-only summary; not authoritative (GC-COOLING-10). */
  usage_days: string;
  active_monday: boolean;
  active_tuesday: boolean;
  active_wednesday: boolean;
  active_thursday: boolean;
  active_friday: boolean;
  active_saturday: boolean;
  active_sunday: boolean;
  active_days_count: number;
  start_hour: number;
  end_hour: number;
  crosses_midnight: boolean;
  daily_occupied_hours: number;
  occupancy_fraction: number;
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
  heat_recovery_efficiency_percent: number;
  fan_power_w: number;
  /** Share (0-1) of fan power dissipated as sensible heat inside the
   * conditioned zone — see ventilation_profile.fan_fraction_dissipated_in_zone
   * on the backend model (GC-COOLING-14). Not yet exposed in the UI; defaults
   * to 1.0 (fan inside the zone), which preserves prior behavior. */
  fan_fraction_dissipated_in_zone: number;
  door_opening_frequency: string;
  window_opening_frequency: string;
  airtightness_n50: number;
  wind_exposure: string;
  infiltration_ach: number;
  /** Value actually used by the solver — see get_effective_infiltration_ach()
   * on the backend model. Read-only, never sent back on PUT. */
  effective_infiltration_ach: number;
  bypass_active: boolean;
  provenance: string;
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
  product_id: number | null;
  name: string;
  category: string;
  quantity: number;
  unit_power_w: number;
  usage_hours_per_day: number;
  simultaneity_percent: number;
}

export interface EquipmentLoadCatalogItem {
  id: number;
  code: string | null;
  name: string;
  category: string;
  unit_power_w: number;
  usage_hours_per_day: number;
  simultaneity_percent: number;
  data_quality: string | null;
}

/** Internal-loads (equipment/lighting/appliances) reference catalog
 * (GC-COOLING-11) — distinct from `getEquipmentCatalog()` below, which
 * lists cooling equipment to *install*, not the loads a study's premises
 * already contain. Never hardcode these values in the frontend. */
export function getEquipmentLoadCatalog() {
  return apiFetch<EquipmentLoadCatalogItem[]>('/equipment-load-catalog');
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

export type EnergyPlusProcessingStatus =
  | 'not_requested'
  | 'disabled'
  | 'translation_failed'
  | 'queued_for_worker'
  | 'simulation_running'
  | 'simulation_unavailable'
  | 'simulation_failed'
  | 'simulation_completed';

export const ENERGYPLUS_TERMINAL_STATUSES: readonly EnergyPlusProcessingStatus[] = [
  'not_requested',
  'disabled',
  'translation_failed',
  'simulation_unavailable',
  'simulation_failed',
  'simulation_completed',
];

/**
 * Two real shapes share this type: POST /calculations (creation response)
 * includes engine/engine_version/request_id; GET /calculations/<job_id>
 * (polling response) does not — those fields are optional here rather than
 * fabricated on the polling path.
 */
export interface CalculationJob {
  job_id: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
  result_id: number | null;
  energyplus_processing_status: EnergyPlusProcessingStatus;
  engine?: string;
  engine_version?: string | null;
  request_id?: string;
  error_message?: string | null;
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
  /** Set once action_validate() promotes this selection to an immutable
   * commercial record; null while still a draft/working "selected" choice. */
  validated_at: string | null;
  validator_id: number | null;
  /** Points to the selection this one replaced, if any (substitution chain,
   * never a destructive edit of history). */
  supersedes_id: number | null;
}

export function listEquipmentSelections(id: number) {
  return apiFetch<EquipmentSelection[]>(`/studies/${id}/equipment-selections`);
}

export function postEquipmentSelection(id: number, productId: number) {
  return apiFetch(`/studies/${id}/equipment-selections`, { method: 'POST', body: { product_id: productId } });
}

export function validateEquipmentSelection(studyId: number, selectionId: number) {
  return apiFetch<EquipmentSelection>(`/studies/${studyId}/equipment-selections/${selectionId}/validate`, {
    method: 'POST',
  });
}
