import { describe, expect, it } from 'vitest';
import { runMercure } from './engine';
import { achToM3h, positiveCoolingDeltaT, wattsToBtuPerHour, wattsToKw } from './conversions';
import { studioStandardInput, westGlazedOfficeInput } from './fixtures';
import golden from './golden_reference';

/** Relative tolerance for TS-vs-Python numeric conformance (GC-COOLING-14
 * pt.5): both are pure-function ports of the same formulas over the same
 * fixtures, so they should agree far tighter than this, but floating-point
 * summation order can differ slightly between the two implementations. */
const RELATIVE_TOLERANCE = 1e-6;

function assertClose(actual: unknown, expected: unknown, path: string): void {
  if (expected !== null && typeof expected === 'object' && !Array.isArray(expected)) {
    for (const [key, value] of Object.entries(expected as Record<string, unknown>)) {
      assertClose((actual as Record<string, unknown>)?.[key], value, `${path}.${key}`);
    }
  } else if (typeof expected === 'number') {
    const tolerance = Math.max(Math.abs(expected) * RELATIVE_TOLERANCE, 1e-9);
    expect(actual as number, path).toBeGreaterThanOrEqual(expected - tolerance);
    expect(actual as number, path).toBeLessThanOrEqual(expected + tolerance);
  } else {
    expect(actual, path).toBe(expected);
  }
}

function summarize(result: ReturnType<typeof runMercure>) {
  return {
    engineCode: result.engineCode,
    engineVersion: result.engineVersion,
    governingScenarioCode: result.governingScenarioCode,
    recommendedCapacityW: result.recommendedCapacityW,
    recommendedCapacityKw: result.recommendedCapacityKw,
    recommendedCapacityBtuH: result.recommendedCapacityBtuH,
    scenarios: Object.fromEntries(
      result.scenarioResults.map((s) => [
        s.scenarioCode,
        {
          sensibleLoadW: s.sensibleLoadW,
          latentLoadW: s.latentLoadW,
          totalLoadW: s.totalLoadW,
          shr: s.shr,
          marginW: s.marginW,
          recommendedLoadW: s.recommendedLoadW,
        },
      ]),
    ),
  };
}

describe('TS/Python conformance (golden reference)', () => {
  it('matches the Python engine for the standard studio', () => {
    const actual = summarize(runMercure(studioStandardInput()));
    assertClose(actual, (golden as any).studioStandard, 'studioStandard');
  });

  it('matches the Python engine for the west-glazed office', () => {
    const actual = summarize(runMercure(westGlazedOfficeInput()));
    assertClose(actual, (golden as any).westGlazedOffice, 'westGlazedOffice');
  });
});

describe('conversions', () => {
  it('converts W to kW', () => {
    expect(wattsToKw(1500)).toBeCloseTo(1.5);
  });

  it('converts W to BTU/h', () => {
    expect(wattsToBtuPerHour(1000)).toBeCloseTo(3412.14, 1);
  });

  it('converts ACH to m3/h', () => {
    expect(achToM3h(0.6, 78)).toBeCloseTo(46.8);
  });

  it('clamps negative delta-T to zero', () => {
    expect(positiveCoolingDeltaT(20, 25)).toBe(0);
    expect(positiveCoolingDeltaT(30, 25)).toBe(5);
  });
});

describe('runMercure — reference cases', () => {
  it('computes a complete result for the standard studio', () => {
    const result = runMercure(studioStandardInput());
    expect(result.scenarioResults).toHaveLength(3);
    expect(result.recommendedCapacityW).toBeGreaterThan(0);
    expect(result.recommendedCapacityKw).toBeCloseTo(result.recommendedCapacityW / 1000);
    expect(result.governingScenarioCode).toBe('prolonged_heatwave');
    for (const scenario of result.scenarioResults) {
      expect(scenario.totalLoadW).toBeGreaterThanOrEqual(scenario.sensibleLoadW);
      expect(scenario.shr).toBeGreaterThan(0);
      expect(scenario.shr).toBeLessThanOrEqual(1);
    }
  });

  it('never returns total load below sensible load', () => {
    const result = runMercure(westGlazedOfficeInput());
    for (const scenario of result.scenarioResults) {
      expect(scenario.totalLoadW).toBeGreaterThanOrEqual(scenario.sensibleLoadW);
    }
  });
});

describe('monotonic properties', () => {
  it('more glazing area does not reduce solar gain', () => {
    const base = studioStandardInput();
    const more = {
      ...base,
      glazing: { facades: base.glazing.facades.map((f) => ({ ...f, areaM2: f.areaM2 * 2 })) },
    };
    const baseResult = runMercure(base).scenarioResults[0];
    const moreResult = runMercure(more).scenarioResults[0];
    const solarBase = baseResult.breakdown.find((b) => b.componentCode === 'solar_glazing')!.totalW;
    const solarMore = moreResult.breakdown.find((b) => b.componentCode === 'solar_glazing')!.totalW;
    expect(solarMore).toBeGreaterThanOrEqual(solarBase);
  });

  it('more occupants does not reduce human gains', () => {
    const base = studioStandardInput();
    const more = { ...base, occupancy: { ...base.occupancy, usualOccupants: base.occupancy.usualOccupants + 2 } };
    const baseResult = runMercure(base).scenarioResults[0];
    const moreResult = runMercure(more).scenarioResults[0];
    const baseGain = baseResult.breakdown.find((b) => b.componentCode === 'occupants_sensible')!.totalW;
    const moreGain = moreResult.breakdown.find((b) => b.componentCode === 'occupants_sensible')!.totalW;
    expect(moreGain).toBeGreaterThan(baseGain);
  });

  it('hotter outdoor air does not reduce ventilation load', () => {
    const base = studioStandardInput();
    const hotter = {
      ...base,
      climateScenarios: base.climateScenarios.map((s) => ({ ...s, outdoorTemperatureC: s.outdoorTemperatureC + 5 })),
    };
    const baseResult = runMercure(base).scenarioResults[0];
    const hotterResult = runMercure(hotter).scenarioResults[0];
    const baseVent = baseResult.breakdown.find((b) => b.componentCode === 'ventilation_sensible')!.totalW;
    const hotterVent = hotterResult.breakdown.find((b) => b.componentCode === 'ventilation_sensible')!.totalW;
    expect(hotterVent).toBeGreaterThanOrEqual(baseVent);
  });

  it('better heat recovery does not increase ventilation sensible load', () => {
    const base = studioStandardInput();
    const better = { ...base, ventilation: { ...base.ventilation, heatRecoveryEfficiency: 0.8 } };
    const baseResult = runMercure(base).scenarioResults[0];
    const betterResult = runMercure(better).scenarioResults[0];
    const baseVent = baseResult.breakdown.find((b) => b.componentCode === 'ventilation_sensible')!.totalW;
    const betterVent = betterResult.breakdown.find((b) => b.componentCode === 'ventilation_sensible')!.totalW;
    expect(betterVent).toBeLessThanOrEqual(baseVent);
  });

  it('a higher setpoint does not increase transmission load', () => {
    const base = studioStandardInput();
    const higherSetpoint = { ...base, comfort: { ...base.comfort, coolingSetpointDayC: base.comfort.coolingSetpointDayC + 2 } };
    const baseResult = runMercure(base).scenarioResults[0];
    const higherResult = runMercure(higherSetpoint).scenarioResults[0];
    const baseWalls = baseResult.breakdown.find((b) => b.componentCode === 'envelope_walls')!.totalW;
    const higherWalls = higherResult.breakdown.find((b) => b.componentCode === 'envelope_walls')!.totalW;
    expect(higherWalls).toBeLessThanOrEqual(baseWalls);
  });
});

describe('errors', () => {
  it('rejects a snapshot without climate scenarios', () => {
    const input = { ...studioStandardInput(), climateScenarios: [] };
    expect(() => runMercure(input)).toThrow('MISSING_CLIMATE_SCENARIO');
  });

  it('rejects invalid geometry', () => {
    const input = { ...studioStandardInput(), geometry: { ...studioStandardInput().geometry, floorAreaM2: 0 } };
    expect(() => runMercure(input)).toThrow('INVALID_GEOMETRY');
  });
});
