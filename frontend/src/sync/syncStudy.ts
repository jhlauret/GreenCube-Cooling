import type { CardinalDirection, EquipmentItem, Facade, StudyDraft } from '../types/study';
import { createEmptyStudyDraft } from '../types/study';
import {
  createEquipmentLoad,
  createStudy,
  deleteEquipmentLoad,
  getOccupancyProfile,
  getStudy,
  getThermalSpecification,
  getThermalSpecificationTemplates,
  getVentilationProfile,
  listEquipmentLoads,
  patchStudy,
  putOccupancyProfile,
  putShading,
  putThermalSpecification,
  putVentilationProfile,
  updateEquipmentLoad,
} from '../api/study';
import { catalogIdForName, catalogIdForProductId } from '../equipment/internalLoadsCatalog';

const USAGE_TYPE_MAP: Record<string, string> = {
  residential: 'housing',
  commerce: 'retail',
};
const USAGE_TYPE_MAP_REVERSE: Record<string, string> = Object.fromEntries(
  Object.entries(USAGE_TYPE_MAP).map(([k, v]) => [v, k]),
);

const ACTIVITY_LEVEL_MAP: Record<string, string> = {
  low: 'light',
};
const ACTIVITY_LEVEL_MAP_REVERSE: Record<string, string> = Object.fromEntries(
  Object.entries(ACTIVITY_LEVEL_MAP).map(([k, v]) => [v, k]),
);

/**
 * The wizard's four facade slots (north/south/east/west) are UI-local
 * names for "front/back/left/right", not fixed compass directions: the
 * "south" slot is the primary/most-glazed facade by convention, and the
 * study's mainOrientation says which way that primary facade actually
 * faces. Rotating the slots by mainOrientation — rather than treating
 * "south" as always meaning geographic south — is what makes the
 * orientation picker in OrientationStep have a real effect on which
 * backend facade orientation (and therefore which MERCURE solar bucket)
 * each slot resolves to (GC-COOLING-09 pt.1-3, audit P1-02).
 */
const COMPASS_ORDER: CardinalDirection[] = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];
export const COMPASS_TO_BACKEND: Record<CardinalDirection, string> = {
  N: 'north',
  NE: 'north_east',
  E: 'east',
  SE: 'south_east',
  S: 'south',
  SO: 'south_west',
  O: 'west',
  NO: 'north_west',
};
const BACKEND_TO_COMPASS: Record<string, CardinalDirection> = Object.fromEntries(
  Object.entries(COMPASS_TO_BACKEND).map(([k, v]) => [v, k as CardinalDirection]),
) as Record<string, CardinalDirection>;
// Offset (in 45°-steps) of each UI slot relative to the primary/"south" slot.
const FACADE_SLOT_OFFSET: Record<Facade, number> = { south: 0, north: 4, east: -2, west: 2 };

export function rotatedOrientation(facade: Facade, mainOrientation: CardinalDirection): string {
  const baseIndex = COMPASS_ORDER.indexOf(mainOrientation);
  const index = (((baseIndex + FACADE_SLOT_OFFSET[facade]) % 8) + 8) % 8;
  return COMPASS_TO_BACKEND[COMPASS_ORDER[index]];
}

/** Inverse of rotatedOrientation: which UI slot does a backend orientation
 * resolve to, given the study's mainOrientation? */
export function facadeSlotForOrientation(backendOrientation: string, mainOrientation: CardinalDirection): Facade | null {
  const compass = BACKEND_TO_COMPASS[backendOrientation];
  if (!compass) return null;
  const baseIndex = COMPASS_ORDER.indexOf(mainOrientation);
  const targetIndex = COMPASS_ORDER.indexOf(compass);
  const offset = (((targetIndex - baseIndex) % 8) + 8) % 8;
  const bySlot = Object.entries(FACADE_SLOT_OFFSET) as [Facade, number][];
  const match = bySlot.find(([, slotOffset]) => (((slotOffset % 8) + 8) % 8) === offset);
  return match ? match[0] : null;
}

/**
 * Each protection type has its own canonical backend `shading_type` and a
 * physically distinct default efficiency, instead of every selected type
 * collapsing into a single hardcoded 'external_blind' (audit P1-03). Since
 * OrientationStep lets several types be selected at once but a facade only
 * has one shading_type, the most effective selected type is the one
 * applied — documented here rather than silently claimed as full
 * multi-layer stacking (GC-COOLING-09 pt.9).
 */
const PROTECTION_TYPE_CONFIG: Record<string, { shadingType: string; efficiencyPercent: number }> = {
  'Stores intérieurs': { shadingType: 'internal_blind', efficiencyPercent: 15 },
  'Ombrage naturel': { shadingType: 'natural', efficiencyPercent: 25 },
  'Casquette solaire': { shadingType: 'overhang', efficiencyPercent: 35 },
  'Brise-soleil': { shadingType: 'brise_soleil', efficiencyPercent: 40 },
  'Stores extérieurs': { shadingType: 'external_blind', efficiencyPercent: 50 },
};

export function resolveDominantProtection(selected: string[]): { shadingType: string; efficiencyPercent: number } | null {
  const configs = selected.map((label) => PROTECTION_TYPE_CONFIG[label]).filter(Boolean);
  if (configs.length === 0) return null;
  return configs.reduce((best, current) => (current.efficiencyPercent > best.efficiencyPercent ? current : best));
}

export function facadeGrossAreaM2(facade: Facade, study: StudyDraft): number {
  const { lengthM, widthM, heightM } = study.model;
  return (facade === 'north' || facade === 'south' ? widthM : lengthM) * heightM;
}

/**
 * Pushes the current local wizard draft to the Odoo backend, creating the
 * backend study on first sync. Called at explicit checkpoints (leaving a
 * step, opening Review, launching a calculation) rather than on every
 * keystroke, since the API has no autosave/debounce contract yet.
 */
export async function syncStudyToBackend(
  study: StudyDraft,
  onBackendId?: (id: number) => void,
  onEquipmentSynced?: (equipment: EquipmentItem[]) => void,
  /**
   * Called with the backend's `updated_at` right after the `PATCH
   * /studies/:id` above succeeds, so the caller (useAutosave) can persist it
   * as StudyDraft.backendUpdatedAt and send it back as `If-Match` on the
   * *next* sync — turning the controller's optional optimistic-locking
   * check (GC-COOLING-02) into something the frontend actually uses.
   */
  onUpdatedAt?: (updatedAt: string | null) => void,
): Promise<number> {
  let backendId = study.backendId;
  if (!backendId) {
    const created = await createStudy(study.name);
    backendId = created.id;
    onBackendId?.(backendId);
  }

  const patched = await patchStudy(
    backendId,
    {
      name: study.name,
      address: study.location.address,
      city: study.location.city,
      latitude: study.location.latitude,
      longitude: study.location.longitude,
      altitude_m: study.location.altitudeM,
      timezone: study.location.timezone,
      environment_type: study.location.environmentType,
      climate_confirmed: study.location.climateConfirmed,
      main_orientation: COMPASS_TO_BACKEND[study.orientation.mainOrientation],
      cooling_setpoint_c: study.comfort.targetTemperatureMinC,
      maximum_acceptable_temperature_c: study.comfort.targetTemperatureMaxC,
      target_humidity_percent: study.comfort.targetHumidityPercent,
      service_level: study.comfort.serviceLevel,
    },
    study.backendUpdatedAt,
  );
  onUpdatedAt?.((patched.updated_at as string | null | undefined) ?? null);

  await putThermalSpecification(backendId, {
    name: `${study.name} — modèle`,
    length_m: study.model.lengthM,
    width_m: study.model.widthM,
    height_m: study.model.heightM,
    wall_u_value: study.model.uValueWm2k,
    // Real per-envelope values, not a fixed ratio of the wall U-value
    // (GC-COOLING-08: a catalog model's actual roof/floor performance must
    // survive the round-trip to Odoo, and "Personnalisé" must be able to
    // set each independently).
    roof_u_value: study.model.roofUValueWm2k,
    floor_u_value: study.model.floorUValueWm2k,
    airtightness_n50: study.model.airtightnessN50,
    // default_infiltration_ach deliberately NOT sent here anymore
    // (GC-COOLING-12): it used to be a client-side "n50 * 0.05"
    // approximation duplicating a conversion the backend now owns as the
    // single documented ach_from_n50()/get_effective_infiltration_ach()
    // (see cooling_study.py._build_mercure_input). airtightness_n50 above
    // is enough for the backend to derive the effective infiltration rate
    // itself; leaving default_infiltration_ach alone preserves whatever
    // was already stored (or the model's own default) for the fallback
    // case where no n50 is available at all.
    // Provenance only: which catalog model (Studio/Bureau/Habitat/Commerce)
    // this study's private specification was forked from, if any
    // (GC-COOLING-08). "Personnalisé" leaves both null.
    ...(study.model.templateId
      ? { source_template_id: study.model.templateId, source_template_version: study.model.templateVersion }
      : {}),
    facades: study.orientation.facades
      .filter((f) => f.enabled)
      .map((f) => {
        const protection = resolveDominantProtection(study.orientation.solarProtections);
        return {
          orientation: rotatedOrientation(f.facade, study.orientation.mainOrientation),
          // The true wall area, not inflated to fit glazing: the backend's
          // own constraint (glazing_area_m2 <= gross_area_m2) is the actual
          // ratio-vitré validation (GC-COOLING-09 pt.4) — artificially
          // growing gross_area_m2 to match glazing would silently defeat it.
          gross_area_m2: facadeGrossAreaM2(f.facade, study),
          glazing_area_m2: f.glazedAreaM2,
          window_u_value: 1.3,
          solar_factor_g: 0.5,
          visible_transmittance: 0.7,
          default_shading_type: protection?.shadingType ?? 'none',
          default_shading_factor: protection ? 1 - protection.efficiencyPercent / 100 : 1.0,
        };
      }),
  });

  await putOccupancyProfile(backendId, {
    usage_type: USAGE_TYPE_MAP[study.usage.usageType] ?? study.usage.usageType,
    usual_occupants: study.usage.usualOccupants,
    maximum_occupants: study.usage.maximumOccupants,
    activity_level: ACTIVITY_LEVEL_MAP[study.usage.activityLevel] ?? study.usage.activityLevel,
    usage_days: study.usage.occupiedDays,
    active_monday: study.usage.occupiedWeekdays.monday,
    active_tuesday: study.usage.occupiedWeekdays.tuesday,
    active_wednesday: study.usage.occupiedWeekdays.wednesday,
    active_thursday: study.usage.occupiedWeekdays.thursday,
    active_friday: study.usage.occupiedWeekdays.friday,
    active_saturday: study.usage.occupiedWeekdays.saturday,
    active_sunday: study.usage.occupiedWeekdays.sunday,
    start_hour: study.usage.occupancyStartHour,
    end_hour: study.usage.occupancyEndHour,
    used_at_night: study.comfort.usedAtNight,
  });

  await putVentilationProfile(backendId, {
    ventilation_type: study.comfort.ventilationSystem,
    airflow_m3h: study.comfort.estimatedAirflowM3h,
    // Real user input, no longer hardcoded by ventilation system
    // (GC-COOLING-12: previously 75%/0% and 0/30W were guessed from
    // ventilationSystem alone regardless of what the user entered).
    heat_recovery_efficiency_percent: study.comfort.heatRecoveryEfficiencyPercent,
    fan_power_w: study.comfort.fanPowerW,
    door_opening_frequency: study.comfort.doorOpeningFrequency,
    window_opening_frequency: study.comfort.windowOpeningFrequency,
    // airtightness_n50/infiltration_ach intentionally not sent from here:
    // the profile's own n50 field is a distinct, optional override of the
    // model-level airtightness_n50 already sent above; leaving it alone
    // means the backend falls back to the model-level value (see
    // cooling_study.py._build_mercure_input), avoiding the previous
    // duplicated "* 0.05" client-side approximation (GC-COOLING-12).
  });

  const dominantProtection = resolveDominantProtection(study.orientation.solarProtections);
  await putShading(
    backendId,
    dominantProtection
      ? study.orientation.facades
          .filter((f) => f.enabled && f.glazedAreaM2 > 0)
          .map((f) => ({
            orientation: rotatedOrientation(f.facade, study.orientation.mainOrientation),
            shading_type: dominantProtection.shadingType,
            efficiency_percent: dominantProtection.efficiencyPercent,
            confirmed: true,
          }))
      : [],
  );

  const syncedEquipment = await syncEquipment(backendId, study.equipment);
  onEquipmentSynced?.(syncedEquipment);

  return backendId;
}

/**
 * Diffs the wizard's equipment lines against the backend by `backendId`
 * (set the first time a line is created) instead of deleting and
 * recreating every line on every save — a full replace broke the audit
 * trail and would race with concurrent edits (GC-COOLING-11, audit finding).
 * Lines the backend has but the wizard no longer selects are deleted;
 * existing lines are updated in place; new selections are created and
 * their backendId is returned so the caller can persist it back into the
 * local store (otherwise the next sync would treat them as new again).
 */
async function syncEquipment(backendId: number, equipment: EquipmentItem[]): Promise<EquipmentItem[]> {
  const existing = await listEquipmentLoads(backendId);
  const existingIds = new Set(existing.map((line) => line.id));
  const selected = equipment.filter((e) => e.selected);
  const keptBackendIds = new Set(selected.map((e) => e.backendId).filter((id): id is number => id != null));

  for (const line of existing) {
    if (!keptBackendIds.has(line.id)) {
      await deleteEquipmentLoad(line.id);
    }
  }

  const synced: EquipmentItem[] = [];
  for (const item of selected) {
    const vals: Record<string, unknown> = {
      name: item.label,
      category: item.category,
      quantity: item.quantity,
      unit_power_w: item.unitPowerW,
      usage_hours_per_day: item.usageHoursPerDay,
      simultaneity_percent: item.simultaneityPercent,
    };
    // Preserve the catalog linkage (GC-COOLING-11) so a reload can match
    // this line back to its catalog card by identity, not just by name.
    if (item.productId != null) vals.product_id = item.productId;
    if (item.backendId != null && existingIds.has(item.backendId)) {
      await updateEquipmentLoad(item.backendId, vals);
      synced.push(item);
    } else {
      const created = await createEquipmentLoad(backendId, vals);
      synced.push({ ...item, backendId: created.id });
    }
  }
  return [...synced, ...equipment.filter((e) => !e.selected)];
}

/**
 * Rebuilds a local StudyDraft from Odoo, so a study created (or edited) in
 * Odoo directly, or from another browser/device, can be reopened in the
 * wizard instead of being invisible to it (audit P0-04). This is a
 * best-effort reverse of syncStudyToBackend: fields with no local
 * equivalent (e.g. equipment catalog linkage, shading schedules) are left
 * at their StudyDraft defaults rather than guessed.
 */
export async function loadStudyFromBackend(backendId: number): Promise<Partial<StudyDraft>> {
  const [study, spec, occupancy, ventilation, equipment, templates] = await Promise.all([
    getStudy(backendId),
    getThermalSpecification(backendId),
    getOccupancyProfile(backendId),
    getVentilationProfile(backendId),
    listEquipmentLoads(backendId),
    getThermalSpecificationTemplates(),
  ]);

  const empty = createEmptyStudyDraft('', '');
  const patch: Partial<StudyDraft> = {
    backendId,
    name: study.name,
    status: study.state === 'calculated' || study.state === 'validated' ? 'calculated' : 'draft',
  };

  const location = study.location as {
    address: string | null;
    city: string | null;
    latitude: number | null;
    longitude: number | null;
    altitude_m: number | null;
    timezone: string | null;
    environment_type: string | null;
    climate_confirmed: boolean;
    main_orientation: string | null;
    location_provenance: string | null;
    location_precision: string | null;
    location_provider: string | null;
    location_resolved_at: string | null;
    climate_scenarios?: Array<{
      id: number;
      scenario_type: string;
      outdoor_temperature_c: number;
      relative_humidity_percent: number;
      solar_radiation_wm2: number;
      wind_speed_ms: number;
      provenance: string;
      dataset_type: string | null;
      checksum: string | null;
      reference_date: string | null;
      data_start: string | null;
      data_end: string | null;
      sample_days: number | null;
      provider_code: string | null;
      provider_version: string | null;
      timezone: string | null;
      license: string | null;
    }>;
  };
  const mainOrientation = location.main_orientation ? BACKEND_TO_COMPASS[location.main_orientation] ?? 'S' : 'S';
  patch.location = {
    ...empty.location,
    address: location.address ?? '',
    city: location.city,
    timezone: location.timezone ?? null,
    latitude: location.latitude,
    longitude: location.longitude,
    altitudeM: location.altitude_m,
    environmentType: (location.environment_type as StudyDraft['location']['environmentType']) ?? null,
    climateConfirmed: location.climate_confirmed,
    locationProvenance: (location.location_provenance as StudyDraft['location']['locationProvenance']) ?? null,
    locationPrecision: (location.location_precision as StudyDraft['location']['locationPrecision']) ?? null,
    locationProvider: location.location_provider ?? null,
    locationResolvedAt: location.location_resolved_at ?? null,
    climateScenarios: (location.climate_scenarios ?? []).map((s) => ({
      id: s.id,
      scenarioType: s.scenario_type as StudyDraft['location']['climateScenarios'][number]['scenarioType'],
      outdoorTemperatureC: s.outdoor_temperature_c,
      relativeHumidityPercent: s.relative_humidity_percent,
      solarRadiationWm2: s.solar_radiation_wm2,
      windSpeedMs: s.wind_speed_ms,
      provenance: s.provenance,
      datasetType: s.dataset_type ?? null,
      checksum: s.checksum ?? null,
      referenceDate: s.reference_date ?? null,
      dataStart: s.data_start ?? null,
      dataEnd: s.data_end ?? null,
      sampleDays: s.sample_days ?? null,
      providerCode: s.provider_code ?? null,
      providerVersion: s.provider_version ?? null,
      timezone: s.timezone ?? null,
      license: s.license ?? null,
    })),
  };

  const comfort = study.comfort as {
    cooling_setpoint_c: number;
    maximum_acceptable_temperature_c: number;
    target_humidity_percent: number;
    service_level: StudyDraft['comfort']['serviceLevel'];
  };

  if (spec) {
    const sourceTemplate = spec.source_template_id ? templates.find((t) => t.id === spec.source_template_id) : null;
    const modelCode = (sourceTemplate?.code.replace(/^gc-/, '') ?? 'custom') as StudyDraft['model']['modelCode'];
    patch.model = {
      ...empty.model,
      modelCode,
      templateId: spec.source_template_id,
      templateVersion: spec.source_template_version,
      lengthM: spec.length_m,
      widthM: spec.width_m,
      heightM: spec.height_m,
      uValueWm2k: spec.wall_u_value,
      roofUValueWm2k: spec.roof_u_value,
      floorUValueWm2k: spec.floor_u_value,
      airtightnessN50: spec.airtightness_n50,
    };
    const facades = empty.orientation.facades.map((f) => {
      const backendFacade = spec.facades.find(
        (bf) => facadeSlotForOrientation(bf.orientation, mainOrientation) === f.facade,
      );
      return backendFacade
        ? { ...f, enabled: true, glazedAreaM2: backendFacade.glazing_area_m2 }
        : { ...f, enabled: false, glazedAreaM2: 0 };
    });
    patch.orientation = { ...empty.orientation, mainOrientation, facades };
  }

  if (occupancy) {
    patch.usage = {
      ...empty.usage,
      usageType: (USAGE_TYPE_MAP_REVERSE[occupancy.usage_type] ?? occupancy.usage_type) as StudyDraft['usage']['usageType'],
      usualOccupants: occupancy.usual_occupants,
      maximumOccupants: occupancy.maximum_occupants,
      occupiedDays: occupancy.usage_days,
      occupiedWeekdays: {
        monday: occupancy.active_monday,
        tuesday: occupancy.active_tuesday,
        wednesday: occupancy.active_wednesday,
        thursday: occupancy.active_thursday,
        friday: occupancy.active_friday,
        saturday: occupancy.active_saturday,
        sunday: occupancy.active_sunday,
      },
      activityLevel: (ACTIVITY_LEVEL_MAP_REVERSE[occupancy.activity_level] ??
        occupancy.activity_level) as StudyDraft['usage']['activityLevel'],
      occupancyStartHour: occupancy.start_hour,
      occupancyEndHour: occupancy.end_hour,
    };
    patch.comfort = {
      ...empty.comfort,
      ...(patch.comfort ?? {}),
      usedAtNight: occupancy.used_at_night,
    };
  }

  patch.comfort = {
    ...empty.comfort,
    ...(patch.comfort ?? {}),
    targetTemperatureMinC: comfort.cooling_setpoint_c,
    targetTemperatureMaxC: comfort.maximum_acceptable_temperature_c,
    targetHumidityPercent: comfort.target_humidity_percent,
    serviceLevel: comfort.service_level,
  };

  if (ventilation) {
    patch.comfort = {
      ...patch.comfort,
      ventilationSystem: ventilation.ventilation_type as StudyDraft['comfort']['ventilationSystem'],
      estimatedAirflowM3h: ventilation.airflow_m3h,
      heatRecoveryEfficiencyPercent: ventilation.heat_recovery_efficiency_percent,
      fanPowerW: ventilation.fan_power_w,
      doorOpeningFrequency: ventilation.door_opening_frequency as StudyDraft['comfort']['doorOpeningFrequency'],
      windowOpeningFrequency: ventilation.window_opening_frequency as StudyDraft['comfort']['windowOpeningFrequency'],
    };
  }

  patch.equipment = equipment.map((line) => ({
    // Matching the backend line back to a catalog id (rather than a fresh
    // random id) is what lets EquipmentStep's checkboxes correctly show a
    // reloaded study's selections as checked (GC-COOLING-11). `product_id`
    // is the reliable identity; name matching is only a fallback for
    // legacy lines saved before `product_id` was round-tripped.
    id: catalogIdForProductId(line.product_id) ?? catalogIdForName(line.name) ?? crypto.randomUUID(),
    backendId: line.id,
    productId: line.product_id,
    label: line.name,
    category: line.category as EquipmentItem['category'],
    quantity: line.quantity,
    unitPowerW: line.unit_power_w,
    usageHoursPerDay: line.usage_hours_per_day,
    simultaneityPercent: line.simultaneity_percent,
    selected: true,
  }));

  return patch;
}
