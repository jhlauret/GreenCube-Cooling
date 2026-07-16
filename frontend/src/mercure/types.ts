export type ScenarioCode = 'reference_summer' | 'hot_weather' | 'prolonged_heatwave';

export interface ClimateScenario {
  code: ScenarioCode;
  label: string;
  outdoorTemperatureC: number;
  outdoorRelativeHumidityPercent: number;
  solarRadiationByFacadeWm2: Record<Facade, number>;
  windSpeedMs: number;
  groundTemperatureC: number;
}

export type Facade = 'north' | 'south' | 'east' | 'west';

export interface EnvelopeSurface {
  areaM2: number;
  uValueWm2k: number;
}

export interface Geometry {
  lengthM: number;
  widthM: number;
  heightM: number;
  floorAreaM2: number;
  volumeM3: number;
}

export interface Envelope {
  walls: EnvelopeSurface;
  roof: EnvelopeSurface;
  floor: EnvelopeSurface;
  floorBoundary: 'ground' | 'outdoor_air' | 'unconditioned_space' | 'conditioned_space' | 'unknown';
  doors: EnvelopeSurface;
  thermalBridgeMode: 'percentage_adjustment' | 'explicit_linear' | 'global_default' | 'none';
  thermalBridgeCorrectionRate: number;
}

export interface GlazingFacade {
  facade: Facade;
  areaM2: number;
  uValueWm2k: number;
  solarFactor: number;
  protectionFactor: number;
  shadeFactor: number;
}

export interface Glazing {
  facades: GlazingFacade[];
}

export interface Occupancy {
  usualOccupants: number;
  maximumOccupants: number;
  occupancyFraction: number;
  sensibleGainPerPersonW: number;
  latentGainPerPersonG_h: number;
}

export interface EquipmentLoad {
  id: string;
  label: string;
  quantity: number;
  unitPowerW: number;
  loadFactor: number;
  simultaneityFactor: number;
  operatingFraction: number;
  fractionDissipatedInZone: number;
  sensibleFraction: number;
  latentFraction: number;
}

export interface Lighting {
  mode: 'power_density' | 'fixtures';
  powerDensityWm2: number;
  usageFraction: number;
  fractionDissipatedInZone: number;
}

export interface Ventilation {
  systemType: 'natural' | 'simple_flow' | 'double_flow' | 'dedicated_mechanical';
  airflowM3h: number;
  heatRecoveryEfficiency: number;
  bypassActive: boolean;
  fanPowerW: number;
  fanFractionDissipatedInZone: number;
  fanOperatingFraction: number;
}

export interface Infiltration {
  method: 'ach' | 'n50_estimated';
  airChangesPerHour: number;
}

export interface Comfort {
  coolingSetpointDayC: number;
  coolingSetpointNightC: number;
  targetRelativeHumidityPercent: number;
  maximumAcceptableTemperatureC: number;
}

export interface MercureInput {
  snapshotId: string;
  snapshotHash: string;
  studyId: string;
  studyVersion: string;
  climateScenarios: ClimateScenario[];
  geometry: Geometry;
  envelope: Envelope;
  glazing: Glazing;
  occupancy: Occupancy;
  equipment: EquipmentLoad[];
  lighting: Lighting;
  ventilation: Ventilation;
  infiltration: Infiltration;
  comfort: Comfort;
  marginFraction: number;
}

export interface ComponentBreakdownEntry {
  componentCode: string;
  label: string;
  sensibleW: number;
  latentW: number;
  totalW: number;
}

export interface MercureWarning {
  code: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  component?: string;
}

export interface MercureScenarioResult {
  scenarioCode: ScenarioCode;
  sensibleLoadW: number;
  latentLoadW: number;
  totalLoadW: number;
  shr: number;
  marginW: number;
  recommendedLoadW: number;
  breakdown: ComponentBreakdownEntry[];
  warnings: MercureWarning[];
  confidenceScore: number;
}

export interface MercureResult {
  engineCode: string;
  engineVersion: string;
  snapshotId: string;
  snapshotHash: string;
  scenarioResults: MercureScenarioResult[];
  governingScenarioCode: ScenarioCode;
  recommendedCapacityW: number;
  recommendedCapacityKw: number;
  recommendedCapacityBtuH: number;
  confidenceScore: number;
  mainLoadDrivers: string[];
  warnings: MercureWarning[];
}
