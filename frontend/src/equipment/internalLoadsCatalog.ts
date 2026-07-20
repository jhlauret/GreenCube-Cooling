import type { EquipmentItem } from '../types/study';

/**
 * Fixed catalog of internal-load templates offered by EquipmentStep. Each
 * `id` is a stable catalog code (not a per-line database id) — it is what
 * lets syncStudy.ts recognize "this line is still the same laptop template"
 * across saves, and what lets loadStudyFromBackend re-check the right boxes
 * when a study created elsewhere is reopened in the wizard.
 */
export const INTERNAL_LOADS_CATALOG: Omit<EquipmentItem, 'selected' | 'backendId'>[] = [
  { id: 'laptop', label: 'Ordinateur portable', category: 'it', quantity: 1, unitPowerW: 45, usageHoursPerDay: 8, simultaneityPercent: 100 },
  { id: 'monitor', label: 'Écran', category: 'it', quantity: 1, unitPowerW: 25, usageHoursPerDay: 8, simultaneityPercent: 100 },
  { id: 'printer', label: 'Imprimante', category: 'it', quantity: 1, unitPowerW: 300, usageHoursPerDay: 1, simultaneityPercent: 20 },
  { id: 'server', label: 'Serveur', category: 'it', quantity: 1, unitPowerW: 800, usageHoursPerDay: 24, simultaneityPercent: 100 },
  { id: 'led', label: 'Éclairage LED', category: 'lighting', quantity: 1, unitPowerW: 15, usageHoursPerDay: 10, simultaneityPercent: 100 },
  { id: 'coffee', label: 'Machine à café', category: 'appliance', quantity: 1, unitPowerW: 1200, usageHoursPerDay: 0.5, simultaneityPercent: 30 },
  { id: 'network', label: 'Réseau (switch / routeur)', category: 'network', quantity: 1, unitPowerW: 30, usageHoursPerDay: 24, simultaneityPercent: 100 },
  { id: 'battery', label: 'Batterie', category: 'other', quantity: 1, unitPowerW: 500, usageHoursPerDay: 2, simultaneityPercent: 50 },
  { id: 'ups', label: 'Onduleur', category: 'other', quantity: 1, unitPowerW: 600, usageHoursPerDay: 24, simultaneityPercent: 100 },
];

export function catalogIdForName(name: string): string | null {
  return INTERNAL_LOADS_CATALOG.find((c) => c.label === name)?.id ?? null;
}
