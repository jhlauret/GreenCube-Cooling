import type { ClimateScenario, MercureInput } from './types';

export function referenceScenario(): ClimateScenario {
  return {
    code: 'reference_summer',
    label: 'Été de référence',
    outdoorTemperatureC: 32,
    outdoorRelativeHumidityPercent: 45,
    solarRadiationByFacadeWm2: { north: 80, south: 350, east: 200, west: 420 },
    windSpeedMs: 2,
    groundTemperatureC: 18,
  };
}

export function hotWeatherScenario(): ClimateScenario {
  return {
    ...referenceScenario(),
    code: 'hot_weather',
    label: 'Forte chaleur',
    outdoorTemperatureC: 37,
    outdoorRelativeHumidityPercent: 35,
  };
}

export function heatwaveScenario(): ClimateScenario {
  return {
    ...referenceScenario(),
    code: 'prolonged_heatwave',
    label: 'Canicule prolongée',
    outdoorTemperatureC: 42,
    outdoorRelativeHumidityPercent: 30,
  };
}

/** Studio standard — 30 m2, 2 occupants, vitrage modéré, faible charge interne. */
export function studioStandardInput(): MercureInput {
  return {
    snapshotId: 'fixture-studio',
    snapshotHash: 'hash-studio',
    studyId: 'study-fixture',
    studyVersion: '1',
    climateScenarios: [referenceScenario(), hotWeatherScenario(), heatwaveScenario()],
    geometry: { lengthM: 6, widthM: 5, heightM: 2.6, floorAreaM2: 30, volumeM3: 78 },
    envelope: {
      walls: { areaM2: 45, uValueWm2k: 0.22 },
      roof: { areaM2: 30, uValueWm2k: 0.18 },
      floor: { areaM2: 30, uValueWm2k: 0.25 },
      floorBoundary: 'ground',
      doors: { areaM2: 2, uValueWm2k: 1.4 },
      thermalBridgeMode: 'percentage_adjustment',
      thermalBridgeCorrectionRate: 0.05,
    },
    glazing: {
      facades: [
        { facade: 'south', areaM2: 4, uValueWm2k: 1.3, solarFactor: 0.5, protectionFactor: 0.7, shadeFactor: 1 },
      ],
    },
    occupancy: {
      usualOccupants: 2,
      maximumOccupants: 3,
      occupancyFraction: 1,
      sensibleGainPerPersonW: 70,
      latentGainPerPersonG_h: 50,
    },
    equipment: [
      {
        id: 'laptop',
        label: 'Ordinateur portable',
        quantity: 1,
        unitPowerW: 45,
        loadFactor: 1,
        simultaneityFactor: 1,
        operatingFraction: 1,
        fractionDissipatedInZone: 1,
        sensibleFraction: 1,
        latentFraction: 0,
      },
    ],
    lighting: { mode: 'power_density', powerDensityWm2: 6, usageFraction: 0.6, fractionDissipatedInZone: 1 },
    ventilation: {
      systemType: 'simple_flow',
      airflowM3h: 60,
      heatRecoveryEfficiency: 0,
      bypassActive: false,
      fanPowerW: 30,
      fanFractionDissipatedInZone: 1,
      fanOperatingFraction: 1,
    },
    infiltration: { method: 'ach', airChangesPerHour: 0.6 },
    comfort: {
      coolingSetpointDayC: 25,
      coolingSetpointNightC: 26,
      targetRelativeHumidityPercent: 50,
      maximumAcceptableTemperatureC: 27,
    },
    marginFraction: 0.15,
  };
}

/** Bureau fortement vitré à l'ouest — sans protection. */
export function westGlazedOfficeInput(): MercureInput {
  const base = studioStandardInput();
  return {
    ...base,
    snapshotId: 'fixture-west-office',
    occupancy: { ...base.occupancy, usualOccupants: 4, maximumOccupants: 6 },
    glazing: {
      facades: [
        { facade: 'west', areaM2: 10, uValueWm2k: 1.3, solarFactor: 0.6, protectionFactor: 1, shadeFactor: 1 },
      ],
    },
    equipment: [
      ...base.equipment,
      {
        id: 'monitor',
        label: 'Écrans',
        quantity: 4,
        unitPowerW: 30,
        loadFactor: 1,
        simultaneityFactor: 1,
        operatingFraction: 1,
        fractionDissipatedInZone: 1,
        sensibleFraction: 1,
        latentFraction: 0,
      },
    ],
  };
}
