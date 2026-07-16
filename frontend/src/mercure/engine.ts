import {
  AIR_DENSITY,
  AIR_SPECIFIC_HEAT,
  LATENT_HEAT_OF_VAPORIZATION,
  MERCURE_ENGINE_CODE,
  MERCURE_ENGINE_VERSION,
} from './constants';
import {
  achToM3h,
  humidityRatioFromTemperatureRh,
  m3hToM3s,
  positiveCoolingDeltaT,
  wattsToBtuPerHour,
  wattsToKw,
} from './conversions';
import type {
  ClimateScenario,
  ComponentBreakdownEntry,
  MercureInput,
  MercureResult,
  MercureScenarioResult,
  MercureWarning,
} from './types';

function transmissionLoads(input: MercureInput, deltaT: number): ComponentBreakdownEntry[] {
  const { envelope } = input;
  const entries: ComponentBreakdownEntry[] = [
    {
      componentCode: 'envelope_walls',
      label: 'Murs',
      sensibleW: envelope.walls.uValueWm2k * envelope.walls.areaM2 * deltaT,
      latentW: 0,
      totalW: 0,
    },
    {
      componentCode: 'envelope_roof',
      label: 'Toiture',
      sensibleW: envelope.roof.uValueWm2k * envelope.roof.areaM2 * deltaT,
      latentW: 0,
      totalW: 0,
    },
    {
      componentCode: 'envelope_doors',
      label: 'Portes',
      sensibleW: envelope.doors.uValueWm2k * envelope.doors.areaM2 * deltaT,
      latentW: 0,
      totalW: 0,
    },
  ];

  // Floor: only a real cooling transmission load if it borders outdoor air or an unconditioned space.
  const floorDeltaT = envelope.floorBoundary === 'ground' ? deltaT * 0.3 : deltaT;
  const floorActive = envelope.floorBoundary !== 'conditioned_space';
  entries.push({
    componentCode: 'envelope_floor',
    label: 'Plancher',
    sensibleW: floorActive ? envelope.floor.uValueWm2k * envelope.floor.areaM2 * floorDeltaT : 0,
    latentW: 0,
    totalW: 0,
  });

  const glazingConduction = input.glazing.facades.reduce(
    (sum, f) => sum + f.uValueWm2k * f.areaM2 * deltaT,
    0,
  );
  entries.push({
    componentCode: 'glazing_conduction',
    label: 'Vitrages (conduction)',
    sensibleW: glazingConduction,
    latentW: 0,
    totalW: 0,
  });

  const envelopeTotal = entries.reduce((sum, e) => sum + e.sensibleW, 0);
  let thermalBridgeW = 0;
  if (envelope.thermalBridgeMode === 'percentage_adjustment') {
    thermalBridgeW = envelopeTotal * envelope.thermalBridgeCorrectionRate;
  }
  entries.push({
    componentCode: 'thermal_bridges',
    label: 'Ponts thermiques',
    sensibleW: thermalBridgeW,
    latentW: 0,
    totalW: 0,
  });

  return entries.map((e) => ({ ...e, totalW: e.sensibleW + e.latentW }));
}

function solarGlazingGain(input: MercureInput, scenario: ClimateScenario): ComponentBreakdownEntry {
  const totalW = input.glazing.facades.reduce((sum, f) => {
    const radiation = scenario.solarRadiationByFacadeWm2[f.facade] ?? 0;
    return sum + f.areaM2 * radiation * f.solarFactor * f.protectionFactor * f.shadeFactor;
  }, 0);
  return { componentCode: 'solar_glazing', label: 'Apports solaires vitrages', sensibleW: totalW, latentW: 0, totalW };
}

function occupancyGains(input: MercureInput): { sensible: ComponentBreakdownEntry; latent: ComponentBreakdownEntry } {
  const { occupancy } = input;
  const effective = occupancy.usualOccupants * occupancy.occupancyFraction;
  const sensibleW = effective * occupancy.sensibleGainPerPersonW;
  const latentW = effective * occupancy.latentGainPerPersonG_h * (LATENT_HEAT_OF_VAPORIZATION.value / 1000) / 3600;
  return {
    sensible: { componentCode: 'occupants_sensible', label: 'Occupants sensible', sensibleW, latentW: 0, totalW: sensibleW },
    latent: { componentCode: 'occupants_latent', label: 'Occupants latent', sensibleW: 0, latentW, totalW: latentW },
  };
}

function equipmentGains(input: MercureInput): { sensible: ComponentBreakdownEntry; latent: ComponentBreakdownEntry } {
  let sensibleW = 0;
  let latentW = 0;
  for (const eq of input.equipment) {
    const activePower = eq.quantity * eq.unitPowerW * eq.loadFactor * eq.simultaneityFactor * eq.operatingFraction;
    const zoneHeat = activePower * eq.fractionDissipatedInZone;
    sensibleW += zoneHeat * eq.sensibleFraction;
    latentW += zoneHeat * eq.latentFraction;
  }
  return {
    sensible: { componentCode: 'equipment_sensible', label: 'Équipements sensible', sensibleW, latentW: 0, totalW: sensibleW },
    latent: { componentCode: 'equipment_latent', label: 'Équipements latent', sensibleW: 0, latentW, totalW: latentW },
  };
}

function lightingGain(input: MercureInput): ComponentBreakdownEntry {
  const { lighting, geometry } = input;
  const sensibleW =
    geometry.floorAreaM2 * lighting.powerDensityWm2 * lighting.usageFraction * lighting.fractionDissipatedInZone;
  return { componentCode: 'lighting', label: 'Éclairage', sensibleW, latentW: 0, totalW: sensibleW };
}

function fanHeatGain(input: MercureInput): ComponentBreakdownEntry {
  const { ventilation } = input;
  const sensibleW = ventilation.fanPowerW * ventilation.fanFractionDissipatedInZone * ventilation.fanOperatingFraction;
  return { componentCode: 'fan_heat', label: 'Chaleur ventilateurs', sensibleW, latentW: 0, totalW: sensibleW };
}

function ventilationLoads(
  input: MercureInput,
  scenario: ClimateScenario,
  deltaT: number,
): { sensible: ComponentBreakdownEntry; latent: ComponentBreakdownEntry } {
  const { ventilation, comfort } = input;
  const flowM3s = m3hToM3s(ventilation.airflowM3h);
  const recoveryEfficiency = ventilation.bypassActive ? 0 : ventilation.heatRecoveryEfficiency;
  const nonRecoveredFactor = 1 - recoveryEfficiency;

  const sensibleW = AIR_DENSITY.value * AIR_SPECIFIC_HEAT.value * flowM3s * deltaT * nonRecoveredFactor;

  const outdoorHumidityRatio = humidityRatioFromTemperatureRh(
    scenario.outdoorTemperatureC,
    scenario.outdoorRelativeHumidityPercent,
  );
  const indoorHumidityRatio = humidityRatioFromTemperatureRh(
    comfort.coolingSetpointDayC,
    comfort.targetRelativeHumidityPercent,
  );
  const humidityRatioDelta = Math.max(0, outdoorHumidityRatio - indoorHumidityRatio);
  const massFlowKgS = flowM3s * AIR_DENSITY.value;
  const latentW = massFlowKgS * humidityRatioDelta * LATENT_HEAT_OF_VAPORIZATION.value * nonRecoveredFactor;

  return {
    sensible: { componentCode: 'ventilation_sensible', label: 'Ventilation sensible', sensibleW, latentW: 0, totalW: sensibleW },
    latent: { componentCode: 'ventilation_latent', label: 'Ventilation latente', sensibleW: 0, latentW, totalW: latentW },
  };
}

function infiltrationLoads(
  input: MercureInput,
  scenario: ClimateScenario,
  deltaT: number,
): { sensible: ComponentBreakdownEntry; latent: ComponentBreakdownEntry } {
  const { infiltration, geometry, comfort } = input;
  const flowM3h = achToM3h(infiltration.airChangesPerHour, geometry.volumeM3);
  const flowM3s = m3hToM3s(flowM3h);
  const sensibleW = AIR_DENSITY.value * AIR_SPECIFIC_HEAT.value * flowM3s * deltaT;

  const outdoorHumidityRatio = humidityRatioFromTemperatureRh(
    scenario.outdoorTemperatureC,
    scenario.outdoorRelativeHumidityPercent,
  );
  const indoorHumidityRatio = humidityRatioFromTemperatureRh(
    comfort.coolingSetpointDayC,
    comfort.targetRelativeHumidityPercent,
  );
  const humidityRatioDelta = Math.max(0, outdoorHumidityRatio - indoorHumidityRatio);
  const massFlowKgS = flowM3s * AIR_DENSITY.value;
  const latentW = massFlowKgS * humidityRatioDelta * LATENT_HEAT_OF_VAPORIZATION.value;

  return {
    sensible: { componentCode: 'infiltration_sensible', label: 'Infiltration sensible', sensibleW, latentW: 0, totalW: sensibleW },
    latent: { componentCode: 'infiltration_latent', label: 'Infiltration latente', sensibleW: 0, latentW, totalW: latentW },
  };
}

function computeConfidenceScore(input: MercureInput, warnings: MercureWarning[]): number {
  let score = 1;
  if (input.infiltration.method === 'n50_estimated') score -= 0.15;
  if (input.envelope.floorBoundary === 'unknown') score -= 0.1;
  if (input.envelope.floorBoundary === 'ground') score -= 0.05;
  score -= warnings.filter((w) => w.level === 'warning').length * 0.05;
  return Math.max(0, Math.min(1, score));
}

function buildWarnings(input: MercureInput, glazingRatio: number): MercureWarning[] {
  const warnings: MercureWarning[] = [];
  if (input.infiltration.method === 'n50_estimated') {
    warnings.push({
      code: 'LOW_CONFIDENCE_INFILTRATION',
      level: 'warning',
      message: "L'infiltration est estimée à partir d'une valeur n50, sans méthode de conversion mesurée.",
      component: 'infiltration',
    });
  }
  if (input.envelope.floorBoundary === 'ground' || input.envelope.floorBoundary === 'unknown') {
    warnings.push({
      code: 'MISSING_GROUND_TEMPERATURE',
      level: 'info',
      message: 'La température de sol est une hypothèse par défaut.',
      component: 'envelope_floor',
    });
  }
  if (glazingRatio > 0.4) {
    warnings.push({
      code: 'HIGH_GLAZING_RATIO',
      level: 'warning',
      message: 'La surface vitrée dépasse 40 % de la surface au sol : vérifier les protections solaires.',
      component: 'glazing',
    });
  }
  return warnings;
}

function computeScenarioResult(input: MercureInput, scenario: ClimateScenario): MercureScenarioResult {
  const deltaT = positiveCoolingDeltaT(scenario.outdoorTemperatureC, input.comfort.coolingSetpointDayC);

  const transmission = transmissionLoads(input, deltaT);
  const solar = solarGlazingGain(input, scenario);
  const occupants = occupancyGains(input);
  const equip = equipmentGains(input);
  const lighting = lightingGain(input);
  const fan = fanHeatGain(input);
  const ventilation = ventilationLoads(input, scenario, deltaT);
  const infiltration = infiltrationLoads(input, scenario, deltaT);

  const breakdown: ComponentBreakdownEntry[] = [
    ...transmission,
    solar,
    occupants.sensible,
    occupants.latent,
    equip.sensible,
    equip.latent,
    lighting,
    fan,
    ventilation.sensible,
    ventilation.latent,
    infiltration.sensible,
    infiltration.latent,
  ];

  const sensibleLoadW = breakdown.reduce((sum, e) => sum + e.sensibleW, 0);
  const latentLoadW = breakdown.reduce((sum, e) => sum + e.latentW, 0);
  const totalLoadW = sensibleLoadW + latentLoadW;
  const shr = totalLoadW > 0 ? sensibleLoadW / totalLoadW : 1;

  const glazingArea = input.glazing.facades.reduce((s, f) => s + f.areaM2, 0);
  const glazingRatio = input.geometry.floorAreaM2 > 0 ? glazingArea / input.geometry.floorAreaM2 : 0;
  const warnings = buildWarnings(input, glazingRatio);

  const marginW = totalLoadW * input.marginFraction;
  const recommendedLoadW = totalLoadW + marginW;

  const withPercentages = breakdown.map((e) => ({
    ...e,
    percentageOfTotal: totalLoadW > 0 ? e.totalW / totalLoadW : 0,
  }));

  return {
    scenarioCode: scenario.code,
    sensibleLoadW,
    latentLoadW,
    totalLoadW,
    shr,
    marginW,
    recommendedLoadW,
    breakdown: withPercentages,
    warnings,
    confidenceScore: computeConfidenceScore(input, warnings),
  };
}

export function selectGoverningScenario(results: MercureScenarioResult[]): MercureScenarioResult {
  return results.reduce((max, r) => (r.recommendedLoadW > max.recommendedLoadW ? r : max), results[0]);
}

export function identifyMainLoadDrivers(result: MercureScenarioResult, topN = 3): string[] {
  return [...result.breakdown]
    .sort((a, b) => b.totalW - a.totalW)
    .slice(0, topN)
    .map((e) => e.label);
}

export function runMercure(input: MercureInput): MercureResult {
  if (input.climateScenarios.length === 0) {
    throw new Error('MISSING_CLIMATE_SCENARIO');
  }
  if (input.geometry.floorAreaM2 <= 0 || input.geometry.volumeM3 <= 0) {
    throw new Error('INVALID_GEOMETRY');
  }

  const scenarioResults = input.climateScenarios.map((s) => computeScenarioResult(input, s));
  const governing = selectGoverningScenario(scenarioResults);
  const allWarnings = scenarioResults.flatMap((r) => r.warnings);
  const overallConfidence =
    scenarioResults.reduce((sum, r) => sum + r.confidenceScore, 0) / scenarioResults.length;

  return {
    engineCode: MERCURE_ENGINE_CODE,
    engineVersion: MERCURE_ENGINE_VERSION,
    snapshotId: input.snapshotId,
    snapshotHash: input.snapshotHash,
    scenarioResults,
    governingScenarioCode: governing.scenarioCode,
    recommendedCapacityW: governing.recommendedLoadW,
    recommendedCapacityKw: wattsToKw(governing.recommendedLoadW),
    recommendedCapacityBtuH: wattsToBtuPerHour(governing.recommendedLoadW),
    confidenceScore: overallConfidence,
    mainLoadDrivers: identifyMainLoadDrivers(governing),
    warnings: allWarnings,
  };
}
