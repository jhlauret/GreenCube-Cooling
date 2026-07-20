/**
 * Not used by any production route (verified: absent from `dist/assets/*.js`
 * — Vite tree-shakes it since nothing in `src/routes` imports it anymore).
 * Kept only as a fixture for `equipment/compatibility.ts`'s own tests and
 * as the reference the real Odoo catalog (`GET /equipment-catalog`) was
 * modeled on. Do not import this from a page/route — use `api/study.ts`'s
 * `getEquipmentCatalog()` instead (audit GC-COOLING-06 pt.11).
 */
export interface CatalogProduct {
  id: string;
  name: string;
  type: string;
  nominalCapacityW: number;
  capacityAt35CW: number;
  capacityAt45CW: number;
  electricalPowerW: number;
  eer: number;
  seer: number;
  shr: number;
  noiseDb: number;
  maxOutdoorTemperatureC: number;
  powerSupply: 'monophase' | 'triphase';
  priceEur: number;
}

export const CATALOG_PRODUCTS: CatalogProduct[] = [
  {
    id: 'gc-split-14',
    name: 'GreenCube Split 1.4 kW',
    type: 'split_wall',
    nominalCapacityW: 1400,
    capacityAt35CW: 1300,
    capacityAt45CW: 1050,
    electricalPowerW: 420,
    eer: 3.3,
    seer: 6.1,
    shr: 0.78,
    noiseDb: 38,
    maxOutdoorTemperatureC: 43,
    powerSupply: 'monophase',
    priceEur: 1190,
  },
  {
    id: 'gc-split-25',
    name: 'GreenCube Split 2.5 kW',
    type: 'split_wall',
    nominalCapacityW: 2500,
    capacityAt35CW: 2350,
    capacityAt45CW: 1900,
    electricalPowerW: 720,
    eer: 3.5,
    seer: 6.4,
    shr: 0.75,
    noiseDb: 41,
    maxOutdoorTemperatureC: 46,
    powerSupply: 'monophase',
    priceEur: 1590,
  },
  {
    id: 'gc-split-35',
    name: 'GreenCube Split 3.5 kW',
    type: 'split_wall',
    nominalCapacityW: 3500,
    capacityAt35CW: 3250,
    capacityAt45CW: 2600,
    electricalPowerW: 1050,
    eer: 3.3,
    seer: 6.2,
    shr: 0.72,
    noiseDb: 44,
    maxOutdoorTemperatureC: 46,
    powerSupply: 'monophase',
    priceEur: 2090,
  },
  {
    id: 'gc-multisplit-50',
    name: 'GreenCube Multi-split 5.0 kW',
    type: 'multi_split',
    nominalCapacityW: 5000,
    capacityAt35CW: 4600,
    capacityAt45CW: 3600,
    electricalPowerW: 1550,
    eer: 3.2,
    seer: 6.0,
    shr: 0.7,
    noiseDb: 47,
    maxOutdoorTemperatureC: 48,
    powerSupply: 'triphase',
    priceEur: 3390,
  },
];
