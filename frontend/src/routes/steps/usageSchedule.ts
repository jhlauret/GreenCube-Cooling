/**
 * Pure schedule math shared by UsageStep's preview and its tests. Kept in
 * its own module (rather than inline in UsageStep.tsx) so the component
 * file only exports the component itself.
 */

/** Daily occupied hours, handling a window that crosses midnight (e.g.
 * 22h -> 6h): mirrors occupancy_profile.py's `_compute_schedule` exactly
 * so this preview doesn't silently diverge from what the backend will
 * actually compute (GC-COOLING-10). */
export function dailyOccupiedHours(startHour: number, endHour: number): number {
  if (endHour === startHour) return 0;
  if (endHour < startHour) return 24 - startHour + endHour;
  return endHour - startHour;
}
