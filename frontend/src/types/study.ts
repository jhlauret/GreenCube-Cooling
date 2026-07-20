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

export interface LocationData {
  address: string;
  city: string | null;
  timezone: string | null;
  latitude: number | null;
  longitude: number | null;
  altitudeM: number | null;
  environmentType: EnvironmentType | null;
  climateConfirmed: boolean;
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
  uValueWm2k: number;
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

export interface UsageData {
  usageType: UsageType;
  usualOccupants: number;
  maximumOccupants: number;
  occupiedDays: string;
  activityLevel: 'low' | 'moderate' | 'high';
  occupancyStartHour: number;
  occupancyEndHour: number;
}

export interface EquipmentItem {
  id: string;
  label: string;
  category: 'it' | 'lighting' | 'appliance' | 'network' | 'other';
  quantity: number;
  unitPowerW: number;
  usageHoursPerDay: number;
  simultaneityPercent: number;
  selected: boolean;
}

export interface ComfortData {
  ventilationSystem: 'natural' | 'simple_flow' | 'double_flow' | 'dedicated_mechanical';
  estimatedAirflowM3h: number;
  targetTemperatureRange: string;
  targetHumidityRange: string;
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
      targetTemperatureRange: '22-25',
      targetHumidityRange: '45-60',
      usedAtNight: false,
      serviceLevel: 'standard',
    },
    completedSteps: [],
  };
}
