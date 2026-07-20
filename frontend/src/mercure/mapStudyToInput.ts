/**
 * Not used by any production route — the equivalent mapping
 * (`_build_mercure_input`) runs server-side in
 * `addons/greencube_cooling/models/cooling_study.py` against real Odoo
 * data, not this client-side draft. Kept only for `engine.test.ts`
 * (audit GC-COOLING-06 pt.11).
 */
import type { StudyDraft } from '../types/study';
import type { ClimateScenario, MercureInput } from './types';

const SOLAR_RADIATION_BY_ENVIRONMENT: Record<string, number> = {
  mountain: 480,
  coastal: 400,
  rural: 420,
  suburban: 380,
  dense_urban: 340,
  industrial: 360,
};

function buildScenarios(study: StudyDraft): ClimateScenario[] {
  const baseTemp = study.location.altitudeM && study.location.altitudeM > 800 ? 34 : 32;
  const peakRadiation = SOLAR_RADIATION_BY_ENVIRONMENT[study.location.environmentType ?? 'suburban'] ?? 380;

  const radiationByFacade = (peak: number) => ({
    north: peak * 0.2,
    south: peak * 0.6,
    east: peak * 0.75,
    west: peak,
  });

  return [
    {
      code: 'reference_summer',
      label: 'Été de référence',
      outdoorTemperatureC: baseTemp,
      outdoorRelativeHumidityPercent: 45,
      solarRadiationByFacadeWm2: radiationByFacade(peakRadiation),
      windSpeedMs: 2,
      groundTemperatureC: 18,
    },
    {
      code: 'hot_weather',
      label: 'Forte chaleur',
      outdoorTemperatureC: baseTemp + 5,
      outdoorRelativeHumidityPercent: 38,
      solarRadiationByFacadeWm2: radiationByFacade(peakRadiation),
      windSpeedMs: 1.5,
      groundTemperatureC: 19,
    },
    {
      code: 'prolonged_heatwave',
      label: 'Canicule prolongée',
      outdoorTemperatureC: baseTemp + 10,
      outdoorRelativeHumidityPercent: 30,
      solarRadiationByFacadeWm2: radiationByFacade(peakRadiation),
      windSpeedMs: 1,
      groundTemperatureC: 21,
    },
  ];
}

export function mapStudyToMercureInput(study: StudyDraft): MercureInput {
  const floorAreaM2 = study.model.lengthM * study.model.widthM;
  const volumeM3 = floorAreaM2 * study.model.heightM;
  const wallAreaM2 = 2 * (study.model.lengthM + study.model.widthM) * study.model.heightM;

  return {
    snapshotId: `${study.id}-snapshot`,
    snapshotHash: `sha-${study.id}-${study.updatedAt}`,
    studyId: study.id,
    studyVersion: study.updatedAt,
    climateScenarios: buildScenarios(study),
    geometry: {
      lengthM: study.model.lengthM,
      widthM: study.model.widthM,
      heightM: study.model.heightM,
      floorAreaM2,
      volumeM3,
    },
    envelope: {
      walls: { areaM2: wallAreaM2, uValueWm2k: study.model.uValueWm2k },
      roof: { areaM2: floorAreaM2, uValueWm2k: study.model.uValueWm2k * 0.9 },
      floor: { areaM2: floorAreaM2, uValueWm2k: study.model.uValueWm2k * 1.1 },
      floorBoundary: 'ground',
      doors: { areaM2: 2, uValueWm2k: 1.4 },
      thermalBridgeMode: 'percentage_adjustment',
      thermalBridgeCorrectionRate: 0.05,
    },
    glazing: {
      facades: study.orientation.facades
        .filter((f) => f.enabled && f.glazedAreaM2 > 0)
        .map((f) => ({
          facade: f.facade,
          areaM2: f.glazedAreaM2,
          uValueWm2k: 1.3,
          solarFactor: 0.5,
          // Kept as a fixed 0.7 placeholder: this file isn't used by any
          // production route (see header comment), only by engine.test.ts's
          // TS/Python parity checks, which don't exercise per-protection-type
          // efficiency (that logic now lives in sync/syncStudy.ts).
          protectionFactor: study.orientation.solarProtections.length > 0 ? 0.7 : 1,
          shadeFactor: 1,
        })),
    },
    occupancy: {
      usualOccupants: study.usage.usualOccupants,
      maximumOccupants: study.usage.maximumOccupants,
      occupancyFraction: 1,
      sensibleGainPerPersonW: study.usage.activityLevel === 'high' ? 100 : study.usage.activityLevel === 'moderate' ? 75 : 60,
      latentGainPerPersonG_h: study.usage.activityLevel === 'high' ? 90 : study.usage.activityLevel === 'moderate' ? 60 : 40,
    },
    equipment: study.equipment.map((e) => ({
      id: e.id,
      label: e.label,
      quantity: e.quantity,
      unitPowerW: e.unitPowerW,
      loadFactor: 1,
      simultaneityFactor: e.simultaneityPercent / 100,
      operatingFraction: Math.min(1, e.usageHoursPerDay / 24),
      fractionDissipatedInZone: 1,
      sensibleFraction: e.category === 'other' ? 0.8 : 1,
      latentFraction: e.category === 'other' ? 0.2 : 0,
    })),
    lighting: {
      mode: 'power_density',
      powerDensityWm2: 6,
      usageFraction: 0.6,
      fractionDissipatedInZone: 1,
    },
    ventilation: {
      systemType: study.comfort.ventilationSystem,
      airflowM3h: study.comfort.estimatedAirflowM3h,
      heatRecoveryEfficiency: study.comfort.ventilationSystem === 'double_flow' ? 0.75 : 0,
      bypassActive: false,
      fanPowerW: study.comfort.ventilationSystem === 'natural' ? 0 : 30,
      fanFractionDissipatedInZone: 1,
      fanOperatingFraction: 1,
    },
    infiltration: {
      method: 'n50_estimated',
      airChangesPerHour: study.model.airtightnessN50 * 0.05,
    },
    comfort: {
      coolingSetpointDayC: study.comfort.targetTemperatureMinC,
      coolingSetpointNightC: study.comfort.targetTemperatureMinC + 1,
      targetRelativeHumidityPercent: study.comfort.targetHumidityPercent,
      maximumAcceptableTemperatureC: study.comfort.targetTemperatureMaxC,
    },
    marginFraction: study.comfort.serviceLevel === 'heatwave_resilience' ? 0.25 : study.comfort.serviceLevel === 'enhanced' ? 0.18 : 0.12,
  };
}
