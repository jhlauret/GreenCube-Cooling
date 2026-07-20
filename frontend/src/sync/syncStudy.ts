import type { EquipmentItem, Facade, StudyDraft } from '../types/study';
import { createEmptyStudyDraft } from '../types/study';
import {
  createEquipmentLoad,
  createStudy,
  deleteEquipmentLoad,
  getOccupancyProfile,
  getStudy,
  getThermalSpecification,
  getVentilationProfile,
  listEquipmentLoads,
  patchStudy,
  putOccupancyProfile,
  putShading,
  putThermalSpecification,
  putVentilationProfile,
} from '../api/study';

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

const FACADE_TO_ORIENTATION: Record<Facade, string> = {
  north: 'north',
  south: 'south',
  east: 'east',
  west: 'west',
};
const ORIENTATION_TO_FACADE: Record<string, Facade> = Object.fromEntries(
  Object.entries(FACADE_TO_ORIENTATION).map(([k, v]) => [v, k as Facade]),
) as Record<string, Facade>;

function facadeGrossAreaM2(facade: Facade, study: StudyDraft): number {
  const { lengthM, widthM, heightM } = study.model;
  return (facade === 'north' || facade === 'south' ? widthM : lengthM) * heightM;
}

function rangeUpperBound(range: string, fallback: number): number {
  const parts = range.split('-');
  const value = Number(parts[1] ?? parts[0]);
  return Number.isFinite(value) ? value : fallback;
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
): Promise<number> {
  let backendId = study.backendId;
  if (!backendId) {
    const created = await createStudy(study.name);
    backendId = created.id;
    onBackendId?.(backendId);
  }

  await patchStudy(backendId, {
    name: study.name,
    address: study.location.address,
    city: study.location.city,
    latitude: study.location.latitude,
    longitude: study.location.longitude,
    altitude_m: study.location.altitudeM,
    environment_type: study.location.environmentType,
    climate_confirmed: study.location.climateConfirmed,
    cooling_setpoint_c: rangeUpperBound(study.comfort.targetTemperatureRange, 25),
    target_humidity_percent: rangeUpperBound(study.comfort.targetHumidityRange, 55),
    service_level: study.comfort.serviceLevel,
  });

  await putThermalSpecification(backendId, {
    name: `${study.name} — modèle`,
    length_m: study.model.lengthM,
    width_m: study.model.widthM,
    height_m: study.model.heightM,
    wall_u_value: study.model.uValueWm2k,
    roof_u_value: study.model.uValueWm2k * 0.9,
    floor_u_value: study.model.uValueWm2k * 1.1,
    airtightness_n50: study.model.airtightnessN50,
    default_infiltration_ach: study.model.airtightnessN50 * 0.05,
    facades: study.orientation.facades
      .filter((f) => f.enabled)
      .map((f) => ({
        orientation: FACADE_TO_ORIENTATION[f.facade],
        gross_area_m2: Math.max(facadeGrossAreaM2(f.facade, study), f.glazedAreaM2),
        glazing_area_m2: f.glazedAreaM2,
        window_u_value: 1.3,
        solar_factor_g: 0.5,
        visible_transmittance: 0.7,
        default_shading_type: study.orientation.solarProtections.length > 0 ? 'external_blind' : 'none',
        default_shading_factor:
          study.orientation.protectionEfficiency === 'high'
            ? 0.5
            : study.orientation.protectionEfficiency === 'medium'
              ? 0.7
              : 0.85,
      })),
  });

  await putOccupancyProfile(backendId, {
    usage_type: USAGE_TYPE_MAP[study.usage.usageType] ?? study.usage.usageType,
    usual_occupants: study.usage.usualOccupants,
    maximum_occupants: study.usage.maximumOccupants,
    activity_level: ACTIVITY_LEVEL_MAP[study.usage.activityLevel] ?? study.usage.activityLevel,
    usage_days: study.usage.occupiedDays,
    start_hour: study.usage.occupancyStartHour,
    end_hour: study.usage.occupancyEndHour,
    used_at_night: study.comfort.usedAtNight,
  });

  await putVentilationProfile(backendId, {
    ventilation_type: study.comfort.ventilationSystem,
    airflow_m3h: study.comfort.estimatedAirflowM3h,
    heat_recovery_efficiency_percent: study.comfort.ventilationSystem === 'double_flow' ? 75 : 0,
    fan_power_w: study.comfort.ventilationSystem === 'natural' ? 0 : 30,
    infiltration_ach: study.model.airtightnessN50 * 0.05,
  });

  await putShading(
    backendId,
    study.orientation.solarProtections.length > 0
      ? study.orientation.facades
          .filter((f) => f.enabled && f.glazedAreaM2 > 0)
          .map((f) => ({
            orientation: FACADE_TO_ORIENTATION[f.facade],
            shading_type: 'external_blind',
            efficiency_percent:
              study.orientation.protectionEfficiency === 'high' ? 50 : study.orientation.protectionEfficiency === 'medium' ? 30 : 15,
            confirmed: true,
          }))
      : [],
  );

  await syncEquipment(backendId, study.equipment);

  return backendId;
}

/**
 * The wizard only tracks a client-generated UUID per equipment line (no
 * backend id round-trips through the store), so lines can't be diffed
 * against the backend by identity. Full replace on every sync is simpler
 * and equally correct for the MVP's line counts (a handful of items).
 */
async function syncEquipment(backendId: number, equipment: EquipmentItem[]) {
  const existing = await listEquipmentLoads(backendId);
  for (const line of existing) {
    await deleteEquipmentLoad(line.id);
  }
  for (const item of equipment.filter((e) => e.selected)) {
    await createEquipmentLoad(backendId, {
      name: item.label,
      category: item.category,
      quantity: item.quantity,
      unit_power_w: item.unitPowerW,
      usage_hours_per_day: item.usageHoursPerDay,
      simultaneity_percent: item.simultaneityPercent,
    });
  }
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
  const [study, spec, occupancy, ventilation, equipment] = await Promise.all([
    getStudy(backendId),
    getThermalSpecification(backendId),
    getOccupancyProfile(backendId),
    getVentilationProfile(backendId),
    listEquipmentLoads(backendId),
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
    environment_type: string | null;
    climate_confirmed: boolean;
  };
  patch.location = {
    ...empty.location,
    address: location.address ?? '',
    city: location.city,
    latitude: location.latitude,
    longitude: location.longitude,
    altitudeM: location.altitude_m,
    environmentType: (location.environment_type as StudyDraft['location']['environmentType']) ?? null,
    climateConfirmed: location.climate_confirmed,
  };

  const comfort = study.comfort as {
    cooling_setpoint_c: number;
    target_humidity_percent: number;
    service_level: StudyDraft['comfort']['serviceLevel'];
  };

  if (spec) {
    patch.model = {
      ...empty.model,
      lengthM: spec.length_m,
      widthM: spec.width_m,
      heightM: spec.height_m,
      uValueWm2k: spec.wall_u_value,
      airtightnessN50: spec.airtightness_n50,
    };
    const facades = empty.orientation.facades.map((f) => {
      const backendFacade = spec.facades.find((bf) => ORIENTATION_TO_FACADE[bf.orientation] === f.facade);
      return backendFacade
        ? { ...f, enabled: true, glazedAreaM2: backendFacade.glazing_area_m2 }
        : { ...f, enabled: false, glazedAreaM2: 0 };
    });
    patch.orientation = { ...empty.orientation, facades };
  }

  if (occupancy) {
    patch.usage = {
      ...empty.usage,
      usageType: (USAGE_TYPE_MAP_REVERSE[occupancy.usage_type] ?? occupancy.usage_type) as StudyDraft['usage']['usageType'],
      usualOccupants: occupancy.usual_occupants,
      maximumOccupants: occupancy.maximum_occupants,
      occupiedDays: occupancy.usage_days,
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
    targetTemperatureRange: String(comfort.cooling_setpoint_c),
    targetHumidityRange: String(comfort.target_humidity_percent),
    serviceLevel: comfort.service_level,
  };

  if (ventilation) {
    patch.comfort = {
      ...patch.comfort,
      ventilationSystem: ventilation.ventilation_type as StudyDraft['comfort']['ventilationSystem'],
      estimatedAirflowM3h: ventilation.airflow_m3h,
    };
  }

  patch.equipment = equipment.map((line) => ({
    id: crypto.randomUUID(),
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
