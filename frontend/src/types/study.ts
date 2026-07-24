export type WizardStepId =
  | 'location'
  | 'model'
  | 'orientation'
  | 'usage'
  | 'equipment'
  | 'comfort'
  | 'review';

export interface WizardStepMeta {
  id: WizardStepId;
  order: number;
  label: string;
  path: string;
}

export const WIZARD_STEPS: WizardStepMeta[] = [
  { id: 'location', order: 1, label: 'Localisation', path: 'location' },
  { id: 'model', order: 2, label: 'Modèle', path: 'model' },
  { id: 'orientation', order: 3, label: 'Orientation', path: 'orientation' },
  { id: 'usage', order: 4, label: 'Usage', path: 'usage' },
  { id: 'equipment', order: 5, label: 'Équipements', path: 'equipment' },
  { id: 'comfort', order: 6, label: 'Ventilation & confort', path: 'comfort' },
  { id: 'review', order: 7, label: 'Vérification', path: 'review' },
];

export type EnvironmentType =
  | 'dense_urban'
  | 'suburban'
  | 'rural'
  | 'mountain'
  | 'coastal'
  | 'industrial';

export type LocationProvenance = 'manual' | 'geocoded' | 'browser' | 'imported';
export type LocationPrecision = 'exact' | 'locality' | 'region' | 'country' | 'unknown';

export type ClimateScenarioType = 'reference_summer' | 'hot_weather' | 'prolonged_heatwave';

/**
 * Mirrors the backend's `_serialize_climate_scenario()` (GC-COOLING-04).
 * Populated only after the study has gone through at least one
 * action_calculate()/create_snapshot() run — empty before that, which the
 * UI must render as "not computed yet", never as an error.
 */
export interface ClimateScenarioData {
  id: number;
  scenarioType: ClimateScenarioType;
  outdoorTemperatureC: number;
  relativeHumidityPercent: number;
  solarRadiationWm2: number;
  windSpeedMs: number;
  provenance: string;
  datasetType: string | null;
  checksum: string | null;
  referenceDate: string | null;
  dataStart: string | null;
  dataEnd: string | null;
  sampleDays: number | null;
  providerCode: string | null;
  providerVersion: string | null;
  timezone: string | null;
  license: string | null;
}

export interface LocationData {
  address: string;
  city: string | null;
  timezone: string | null;
  latitude: number | null;
  longitude: number | null;
  altitudeM: number | null;
  environmentType: EnvironmentType | null;
  climateConfirmed: boolean;
  /**
   * How the current coordinates were obtained (GC-COOLING-03). Set by the
   * backend when POST /studies/:id/confirm-location succeeds — never
   * written directly by the UI, so a stale local guess can't masquerade as
   * a confirmed provenance.
   */
  locationProvenance: LocationProvenance | null;
  locationPrecision: LocationPrecision | null;
  locationProvider: string | null;
  locationResolvedAt: string | null;
  /** Empty until a calculation has run at least once — see ClimateScenarioData. */
  climateScenarios: ClimateScenarioData[];
}

export type GreenCubeModelCode = 'studio' | 'office' | 'living' | 'commerce' | 'custom';

export interface ModelData {
  modelCode: GreenCubeModelCode;
  /**
   * Odoo id of the catalog `greencube.thermal.specification` this model was
   * applied from, or null for "Personnalisé" (freeform dimensions). Set by
   * ModelStep when the user picks a real catalog card — never hand-written
   * (GC-COOLING-08: the four model choices must have a real, versioned,
   * Odoo-backed effect instead of only changing a decorative label).
   */
  templateId: number | null;
  templateVersion: string | null;
  lengthM: number;
  widthM: number;
  heightM: number;
  wallComposition: string;
  insulationMm: number;
  glazingType: string;
  /** Wall U-value, W/m².K. */
  uValueWm2k: number;
  /**
   * Roof and floor U-values, W/m².K. Kept as their own fields (not derived
   * from uValueWm2k via a fixed ratio) so a catalog model's real envelope
   * performance is preserved end to end, and so "Personnalisé" can set each
   * independently — GC-COOLING-08 explicitly requires wall/roof/floor to be
   * distinct, traceable values, not a single average multiplied by a
   * hardcoded constant.
   */
  roofUValueWm2k: number;
  floorUValueWm2k: number;
  airtightnessN50: number;
}

export type CardinalDirection = 'N' | 'NE' | 'E' | 'SE' | 'S' | 'SO' | 'O' | 'NO';
export type Facade = 'north' | 'south' | 'east' | 'west';

export interface FacadeGlazing {
  facade: Facade;
  enabled: boolean;
  glazedAreaM2: number;
}

export interface OrientationData {
  mainOrientation: CardinalDirection;
  facades: FacadeGlazing[];
  /**
   * Labels from OrientationStep's PROTECTIONS list. Each has a fixed
   * canonical efficiency (see sync/syncStudy.ts's PROTECTION_TYPE_CONFIG) —
   * there is deliberately no separate low/medium/high efficiency knob
   * anymore, since that used to be a decorative field with no UI control
   * and no effect distinct from the protection type itself (audit P1-03).
   */
  solarProtections: string[];
}

export type UsageType =
  | 'office'
  | 'residential'
  | 'meeting_room'
  | 'commerce'
  | 'workshop'
  | 'medical'
  | 'server_room'
  | 'other';

export type Weekday = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';

export const WEEKDAYS: Weekday[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

export interface UsageData {
  usageType: UsageType;
  usualOccupants: number;
  maximumOccupants: number;
  /**
   * Structured weekly calendar (GC-COOLING-10) — the actual source of
   * truth sent to the backend's active_<weekday> boolean fields. Replaces
   * the previous plan of storing the schedule as free text: a string like
   * "Lun-Ven" can't be validated or safely consumed by the solver, and
   * (before this fix) `occupiedDays` was never even exposed in the UI —
   * days were only ever silently carried through at their default value.
   */
  occupiedWeekdays: Record<Weekday, boolean>;
  /** @deprecated Legacy display-only summary kept for backend round-trip
   * compatibility (backend `usage_days`); `occupiedWeekdays` is authoritative. */
  occupiedDays: string;
  activityLevel: 'low' | 'moderate' | 'high';
  occupancyStartHour: number;
  occupancyEndHour: number;
}

export interface EquipmentItem {
  id: string;
  /** Odoo `greencube.cooling.equipment.load` id once this line has been
   * synced at least once — lets syncStudy diff against the backend instead
   * of deleting and recreating every line on every save (GC-COOLING-11). */
  backendId?: number | null;
  /** Odoo `product.template` id of the catalog entry this line was added
   * from, or `null`/absent for a fully custom line. Used to match a
   * reloaded backend line back to its catalog card by identity instead of
   * by (possibly edited/translated) name (GC-COOLING-11). */
  productId?: number | null;
  label: string;
  /** Mirrors the backend `greencube.cooling.equipment.load.category`
   * Selection exactly (GC-COOLING-11) — widened from a 5-value subset so
   * catalog entries like batteries/UPS can carry their real category
   * instead of being folded into 'other'. */
  category: 'it' | 'lighting' | 'appliance' | 'kitchen' | 'network' | 'battery' | 'inverter' | 'medical' | 'machine' | 'other';
  quantity: number;
  unitPowerW: number;
  usageHoursPerDay: number;
  simultaneityPercent: number;
  selected: boolean;
}

export interface ComfortData {
  ventilationSystem: 'natural' | 'simple_flow' | 'double_flow' | 'dedicated_mechanical';
  estimatedAirflowM3h: number;
  /** Real user input, no longer inferred from ventilationSystem (GC-COOLING-12:
   * the backend used to receive a hardcoded 75%/0% guess instead of what the
   * user actually has installed). Meaningful mainly for double_flow/dedicated
   * systems; 0 for natural/simple_flow. */
  heatRecoveryEfficiencyPercent: number;
  /** Real user input, no longer inferred from ventilationSystem (same
   * GC-COOLING-12 gap as heatRecoveryEfficiencyPercent). */
  fanPowerW: number;
  /** Stored on the ventilation profile and actually used by the backend's
   * get_effective_infiltration_ach() (door/window opening was previously
   * displayed nowhere in the UI and had zero effect on the calculation). */
  doorOpeningFrequency: 'rare' | 'occasional' | 'frequent' | 'continuous';
  windowOpeningFrequency: 'rare' | 'occasional' | 'frequent' | 'continuous';
  /** Day setpoint (backend `cooling_setpoint_c`) — the target/ideal
   * temperature, not just the low end of a display range. */
  targetTemperatureMinC: number;
  /** Max acceptable temperature before comfort is considered breached
   * (backend `maximum_acceptable_temperature_c`). Both bounds are sent to
   * MERCURE — previously only the upper bound reached the backend and the
   * lower bound was silently dropped (GC-COOLING-12). */
  targetTemperatureMaxC: number;
  /** MERCURE only models a single humidity target, so this is a value, not
   * a range — kept as one field to avoid implying a second bound that
   * would never be used. */
  targetHumidityPercent: number;
  usedAtNight: boolean;
  serviceLevel: 'standard' | 'enhanced' | 'heatwave_resilience';
}

export interface StudyDraft {
  id: string;
  backendId: number | null;
  name: string;
  createdAt: string;
  updatedAt: string;
  /** Set by the autosave hook after a successful syncStudyToBackend call —
   * compared against `updatedAt` to derive the dirty/clean sync status
   * shown in AppHeader (audit P0-04's "cache de brouillon contrôlé"). */
  lastSyncedAt: string | null;
  /**
   * Backend `write_date` (ISO) as of the last successful sync — sent back
   * as the `If-Match` header on the next PATCH so the controller can detect
   * a concurrent edit from another tab/user and answer 409 instead of one
   * writer silently overwriting the other (GC-COOLING-06 §17).
   */
  backendUpdatedAt: string | null;
  status: 'draft' | 'ready' | 'calculated';
  location: LocationData;
  model: ModelData;
  orientation: OrientationData;
  usage: UsageData;
  equipment: EquipmentItem[];
  comfort: ComfortData;
  completedSteps: WizardStepId[];
  selectedEquipmentProductId: string | null;
}

export function createEmptyStudyDraft(id: string, name: string): StudyDraft {
  const now = new Date().toISOString();
  return {
    id,
    backendId: null,
    lastSyncedAt: null,
    backendUpdatedAt: null,
    name,
    createdAt: now,
    updatedAt: now,
    status: 'draft',
    location: {
      address: '',
      city: null,
      timezone: null,
      latitude: null,
      longitude: null,
      altitudeM: null,
      environmentType: null,
      climateConfirmed: false,
      locationProvenance: null,
      locationPrecision: null,
      locationProvider: null,
      locationResolvedAt: null,
      climateScenarios: [],
    },
    model: {
      modelCode: 'studio',
      templateId: null,
      templateVersion: null,
      lengthM: 4,
      widthM: 2.5,
      heightM: 2.5,
      wallComposition: 'CLT + isolation biosourcée',
      insulationMm: 120,
      glazingType: 'Double vitrage low-E',
      uValueWm2k: 0.18,
      roofUValueWm2k: 0.16,
      floorUValueWm2k: 0.2,
      airtightnessN50: 0.6,
    },
    orientation: {
      mainOrientation: 'S',
      facades: [
        { facade: 'north', enabled: false, glazedAreaM2: 0 },
        { facade: 'south', enabled: true, glazedAreaM2: 4 },
        { facade: 'east', enabled: false, glazedAreaM2: 0 },
        { facade: 'west', enabled: false, glazedAreaM2: 0 },
      ],
      solarProtections: [],
    },
    usage: {
      usageType: 'office',
      usualOccupants: 2,
      maximumOccupants: 4,
      occupiedWeekdays: {
        monday: true,
        tuesday: true,
        wednesday: true,
        thursday: true,
        friday: true,
        saturday: false,
        sunday: false,
      },
      occupiedDays: 'Lun-Ven',
      activityLevel: 'moderate',
      occupancyStartHour: 8,
      occupancyEndHour: 18,
    },
    equipment: [],
    selectedEquipmentProductId: null,
    comfort: {
      ventilationSystem: 'simple_flow',
      estimatedAirflowM3h: 60,
      heatRecoveryEfficiencyPercent: 0,
      fanPowerW: 30,
      doorOpeningFrequency: 'occasional',
      windowOpeningFrequency: 'occasional',
      targetTemperatureMinC: 22,
      targetTemperatureMaxC: 25,
      targetHumidityPercent: 55,
      usedAtNight: false,
      serviceLevel: 'standard',
    },
    completedSteps: [],
  };
}
