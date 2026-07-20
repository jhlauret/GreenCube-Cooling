import { describe, expect, it } from 'vitest';
import {
  facadeGrossAreaM2,
  facadeSlotForOrientation,
  resolveDominantProtection,
  rotatedOrientation,
} from './syncStudy';
import { createEmptyStudyDraft } from '../types/study';
import type { CardinalDirection, Facade } from '../types/study';

describe('rotatedOrientation', () => {
  it('is the identity mapping when mainOrientation is S (the UI default)', () => {
    expect(rotatedOrientation('south', 'S')).toBe('south');
    expect(rotatedOrientation('north', 'S')).toBe('north');
    expect(rotatedOrientation('east', 'S')).toBe('east');
    expect(rotatedOrientation('west', 'S')).toBe('west');
  });

  it('rotates all four slots consistently when mainOrientation is SE', () => {
    expect(rotatedOrientation('south', 'SE')).toBe('south_east');
    expect(rotatedOrientation('north', 'SE')).toBe('north_west');
    expect(rotatedOrientation('east', 'SE')).toBe('north_east');
    expect(rotatedOrientation('west', 'SE')).toBe('south_west');
  });

  it('rotates 180 degrees when mainOrientation is N', () => {
    expect(rotatedOrientation('south', 'N')).toBe('north');
    expect(rotatedOrientation('north', 'N')).toBe('south');
    expect(rotatedOrientation('east', 'N')).toBe('west');
    expect(rotatedOrientation('west', 'N')).toBe('east');
  });

  it('never produces the same backend orientation for two different slots', () => {
    for (const main of ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'] as CardinalDirection[]) {
      const results = (['north', 'south', 'east', 'west'] as Facade[]).map((f) => rotatedOrientation(f, main));
      expect(new Set(results).size).toBe(4);
    }
  });
});

describe('facadeSlotForOrientation (inverse of rotatedOrientation)', () => {
  it('round-trips for every combination of slot and main orientation', () => {
    for (const main of ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'] as CardinalDirection[]) {
      for (const facade of ['north', 'south', 'east', 'west'] as Facade[]) {
        const backendOrientation = rotatedOrientation(facade, main);
        expect(facadeSlotForOrientation(backendOrientation, main)).toBe(facade);
      }
    }
  });

  it('returns null for an orientation string it does not recognize', () => {
    expect(facadeSlotForOrientation('not_a_real_orientation', 'S')).toBeNull();
  });
});

describe('resolveDominantProtection', () => {
  it('returns null when nothing is selected', () => {
    expect(resolveDominantProtection([])).toBeNull();
  });

  it('picks the single selected protection', () => {
    expect(resolveDominantProtection(['Casquette solaire'])).toEqual({
      shadingType: 'overhang',
      efficiencyPercent: 35,
    });
  });

  it('picks the most efficient one when several are selected', () => {
    const result = resolveDominantProtection(['Stores intérieurs', 'Stores extérieurs', 'Ombrage naturel']);
    expect(result).toEqual({ shadingType: 'external_blind', efficiencyPercent: 50 });
  });

  it('ignores unrecognized labels', () => {
    expect(resolveDominantProtection(['Not a real protection'])).toBeNull();
  });
});

describe('facadeGrossAreaM2', () => {
  it('uses width for north/south slots and length for east/west slots', () => {
    const study = createEmptyStudyDraft('id', 'name');
    study.model.lengthM = 6;
    study.model.widthM = 3;
    study.model.heightM = 2.5;

    expect(facadeGrossAreaM2('south', study)).toBeCloseTo(3 * 2.5);
    expect(facadeGrossAreaM2('north', study)).toBeCloseTo(3 * 2.5);
    expect(facadeGrossAreaM2('east', study)).toBeCloseTo(6 * 2.5);
    expect(facadeGrossAreaM2('west', study)).toBeCloseTo(6 * 2.5);
  });
});
