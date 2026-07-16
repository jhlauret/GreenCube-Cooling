import { WATTS_PER_BTU_H } from './constants';

export function wattsToKw(w: number): number {
  return w / 1000;
}

export function wattsToBtuPerHour(w: number): number {
  return w / WATTS_PER_BTU_H;
}

export function m3hToM3s(m3h: number): number {
  return m3h / 3600;
}

export function achToM3h(ach: number, volumeM3: number): number {
  if (ach < 0) throw new Error('INVALID_UNIT: ach must be >= 0');
  if (volumeM3 < 0) throw new Error('INVALID_UNIT: volume must be >= 0');
  return ach * volumeM3;
}

/**
 * Approximation (Tetens) of saturation vapor pressure, then humidity ratio.
 * Sufficient for MVP pre-dimensioning; not a full psychrometrics library.
 */
export function humidityRatioFromTemperatureRh(
  temperatureC: number,
  relativeHumidityPercent: number,
  pressurePa = 101_325,
): number {
  const svp = 610.94 * Math.exp((17.625 * temperatureC) / (temperatureC + 243.04));
  const vaporPressure = (relativeHumidityPercent / 100) * svp;
  return (0.622 * vaporPressure) / (pressurePa - vaporPressure);
}

/** Never allow a negative cooling delta-T to create a cooling load. */
export function positiveCoolingDeltaT(outdoorC: number, indoorC: number): number {
  return Math.max(0, outdoorC - indoorC);
}
