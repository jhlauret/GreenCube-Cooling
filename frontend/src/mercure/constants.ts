/**
 * Centralized physical constants for MERCURE.
 * Per README_GC-COOLING-14_MERCURE.md: every constant must be named,
 * valued, unit-tagged, sourced and versioned.
 */
export interface PhysicalConstant {
  name: string;
  value: number;
  unit: string;
  source: string;
  version: string;
}

export const AIR_DENSITY: PhysicalConstant = {
  name: 'air_density',
  value: 1.2,
  unit: 'kg/m3',
  source: 'ASHRAE Fundamentals, 20 C sea level approximation',
  version: '1.0',
};

export const AIR_SPECIFIC_HEAT: PhysicalConstant = {
  name: 'air_specific_heat',
  value: 1006,
  unit: 'J/kg.K',
  source: 'ASHRAE Fundamentals',
  version: '1.0',
};

export const LATENT_HEAT_OF_VAPORIZATION: PhysicalConstant = {
  name: 'latent_heat_of_vaporization',
  value: 2_501_000,
  unit: 'J/kg',
  source: 'ASHRAE Fundamentals, 0 C reference',
  version: '1.0',
};

export const WATTS_PER_BTU_H = 0.29307107;

export const MERCURE_ENGINE_CODE = 'MERCURE';
export const MERCURE_ENGINE_VERSION = '1.0.0';
export const MERCURE_METHOD_VERSION = '1.0';
