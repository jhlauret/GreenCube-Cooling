import { getEquipmentLoadCatalog, type EquipmentLoadCatalogItem } from '../api/study';
import type { EquipmentItem } from '../types/study';

/**
 * Internal-loads (equipment/lighting/appliances) catalog fetched from Odoo
 * (`GET /equipment-load-catalog`) — GC-COOLING-11. This module used to
 * export a static, hardcoded array of templates (laptop, monitor, ...),
 * which meant the list of equipment offered by the Equipment step could
 * never come from Odoo, be corrected, or be extended without a frontend
 * deploy. Odoo (`product.template` with `is_internal_load_equipment`) is
 * now the only source of these values; this module only caches the last
 * fetch so the synchronous lookups below (used by the sync layer, which
 * has no React lifecycle of its own) don't need to re-fetch on every call.
 */
export interface InternalLoadCatalogEntry {
  /** Stable catalog code (backend `internal_load_code`), used as the
   * frontend-local `EquipmentItem.id`. */
  id: string;
  productId: number;
  label: string;
  category: EquipmentItem['category'];
  unitPowerW: number;
  usageHoursPerDay: number;
  simultaneityPercent: number;
}

let cache: InternalLoadCatalogEntry[] = [];

function toEntry(item: EquipmentLoadCatalogItem): InternalLoadCatalogEntry | null {
  if (!item.code) return null; // Not usable as a stable card id — skip rather than guess.
  return {
    id: item.code,
    productId: item.id,
    label: item.name,
    category: (item.category ?? 'other') as EquipmentItem['category'],
    unitPowerW: item.unit_power_w,
    usageHoursPerDay: item.usage_hours_per_day,
    simultaneityPercent: item.simultaneity_percent,
  };
}

/** Fetches the catalog from Odoo and refreshes the local cache used by the
 * synchronous lookups below. Callers (e.g. `EquipmentStep`) should still
 * hold their own loading/error state for the UI — this function does not
 * swallow rejections. */
export async function fetchInternalLoadsCatalog(): Promise<InternalLoadCatalogEntry[]> {
  const data = await getEquipmentLoadCatalog();
  cache = data.map(toEntry).filter((e): e is InternalLoadCatalogEntry => e !== null);
  return cache;
}

/** Last catalog successfully fetched via `fetchInternalLoadsCatalog()`, or
 * `[]` before the first fetch resolves. */
export function getCachedInternalLoadsCatalog(): InternalLoadCatalogEntry[] {
  return cache;
}

/** Matches a reloaded backend equipment-load line back to its catalog
 * card by `product_id` — the reliable identity, unlike name matching
 * below, which only exists for legacy custom lines created before
 * `product_id` was round-tripped. */
export function catalogIdForProductId(productId: number | null | undefined): string | null {
  if (productId == null) return null;
  return cache.find((c) => c.productId === productId)?.id ?? null;
}

/** Fallback for lines with no `product_id` (created before GC-COOLING-11,
 * or genuinely custom lines whose name happens to match a catalog label). */
export function catalogIdForName(name: string): string | null {
  return cache.find((c) => c.label === name)?.id ?? null;
}
