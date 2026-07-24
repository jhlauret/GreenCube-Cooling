# -*- coding: utf-8 -*-
"""TransactionCase tests exercising the module through the real Odoo ORM.

These complement tests/test_mercure_engine.py and tests/test_compatibility.py
(pure-Python, ORM-independent) by covering the parts of GC-COOLING-01 §27
that only make sense against a live registry: status cycle, revision
locking, result/component immutability, multi-company ACL/record rules and
action_calculate() end-to-end. Also covers GC-COOLING-13's backend slice:
structured validation, immutable calculation snapshots, and calculation
sourced from the frozen snapshot rather than live study data.
"""
import json

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


def _thermal_spec_vals(company_id=False, code="GC-STD-30"):
    return {
        "name": "Studio standard 30m2",
        "code": code,
        "version": "1.0",
        "length_m": 6.0,
        "width_m": 5.0,
        "height_m": 2.6,
        "wall_u_value": 0.22,
        "roof_u_value": 0.18,
        "floor_u_value": 0.25,
        "thermal_mass_level": "medium",
        "thermal_bridge_factor": 0.05,
        "default_infiltration_ach": 0.6,
        **({"company_id": company_id} if company_id else {}),
    }


@tagged("post_install", "-at_install")
class TestCoolingStudyLifecycle(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        technician_group = cls.env.ref("greencube_cooling.group_greencube_cooling_technician")
        cls.env.user.write({"groups_id": [(4, technician_group.id)]})
        cls.spec = cls.env["greencube.thermal.specification"].create(_thermal_spec_vals())
        cls.env["greencube.thermal.facade"].create(
            {
                "thermal_specification_id": cls.spec.id,
                "orientation": "south",
                "gross_area_m2": 10.0,
                "glazing_area_m2": 4.0,
                "window_u_value": 1.3,
                "solar_factor_g": 0.5,
                "default_shading_factor": 0.7,
            }
        )

    def _create_study(self, **overrides):
        vals = {
            "name": "Étude test",
            "thermal_specification_id": self.spec.id,
            "latitude": 43.6,
            "longitude": 3.9,
            "environment_type": "suburban",
            "climate_confirmed": True,
        }
        vals.update(overrides)
        return self.env["greencube.cooling.study"].create(vals)

    def _fill_required_sections(self, study):
        self.env["greencube.cooling.occupancy.profile"].create(
            {
                "study_id": study.id,
                "usage_type": "housing",
                "usual_occupants": 2,
                "maximum_occupants": 3,
            }
        )
        self.env["greencube.cooling.equipment.load"].create(
            {
                "study_id": study.id,
                "name": "Ordinateur portable",
                "category": "it",
                "quantity": 1,
                "unit_power_w": 45,
                "usage_hours_per_day": 8,
                "simultaneity_percent": 100,
            }
        )
        self.env["greencube.cooling.ventilation.profile"].create(
            {
                "study_id": study.id,
                "ventilation_type": "simple_flow",
                "airflow_m3h": 60,
                "heat_recovery_efficiency_percent": 0,
                "infiltration_ach": 0.6,
            }
        )

    # -- reference + creation -----------------------------------------

    def test_create_assigns_sequence_reference(self):
        study = self._create_study()
        self.assertTrue(study.reference)
        self.assertEqual(study.root_study_id, study)

    # -- status cycle ---------------------------------------------------

    def test_status_cycle_draft_to_validated(self):
        study = self._create_study()
        self.assertEqual(study.state, "draft")

        # Missing occupancy -> incomplete
        study.action_mark_ready()
        self.assertEqual(study.state, "incomplete")

        self._fill_required_sections(study)
        study.action_mark_ready()
        self.assertEqual(study.state, "ready")

        study.action_create_snapshot()
        self.assertTrue(study.input_snapshot_hash)

        result = study.action_calculate()
        self.assertEqual(study.state, "calculated")
        self.assertEqual(result.state, "success")
        self.assertGreater(result.recommended_capacity_w, 0)

        study.action_validate()
        self.assertEqual(study.state, "validated")
        self.assertTrue(study.validation_date)
        self.assertEqual(study.validator_id, self.env.user)

    def test_validate_requires_calculated_state(self):
        study = self._create_study()
        with self.assertRaises(UserError):
            study.action_validate()

    # -- revision + locking ----------------------------------------------

    def test_write_blocked_on_validated_study(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.action_create_snapshot()
        study.action_calculate()
        study.action_validate()

        with self.assertRaises(UserError):
            study.write({"name": "Renamed after validation"})

        # notes/state-adjacent fields remain writable per LOCKED_STATES logic
        study.write({"notes": "<p>ok</p>"})
        self.assertIn("ok", study.notes)

    def test_create_revision_copies_sublines_and_locks_parent_link(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.action_create_snapshot()
        study.action_calculate()
        study.action_validate()

        action = study.action_create_revision()
        revision = self.env["greencube.cooling.study"].browse(action["res_id"])

        self.assertEqual(revision.state, "draft")
        self.assertEqual(revision.revision_number, 2)
        self.assertEqual(revision.parent_study_id, study)
        self.assertEqual(revision.root_study_id, study)
        self.assertEqual(len(revision.occupancy_profile_ids), 1)
        self.assertEqual(len(revision.equipment_load_ids), 1)
        self.assertEqual(len(revision.ventilation_profile_ids), 1)
        # the active/successful result must NOT be copied onto the revision
        self.assertFalse(revision.result_ids)
        # the root study is preserved across revisions
        self.assertEqual(revision.root_study_id, study.root_study_id)

    # -- result / component immutability ----------------------------------

    def test_result_and_component_are_immutable(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.action_create_snapshot()
        result = study.action_calculate()
        component = result.component_ids[:1]
        self.assertTrue(component)

        with self.assertRaises(UserError):
            result.write({"sensible_load_w": 0.0})
        with self.assertRaises(UserError):
            result.unlink()
        with self.assertRaises(UserError):
            component.write({"total_w": 0.0})
        with self.assertRaises(UserError):
            component.unlink()

        # Superseding the state is the one allowed mutation.
        result.write({"state": "superseded"})
        self.assertEqual(result.state, "superseded")

    def test_thermal_specification_locks_calculatory_fields_once_used(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.action_create_snapshot()
        study.action_calculate()
        study.action_validate()

        self.assertTrue(self.spec.is_locked)
        with self.assertRaises(UserError):
            self.spec.write({"wall_u_value": 0.5})

    # -- GC-COOLING-13: structured validation ----------------------------

    def test_get_validation_blocks_on_missing_occupancy(self):
        study = self._create_study()
        validation = study.get_validation()
        self.assertFalse(validation["ready"])
        self.assertGreater(validation["blocking_count"], 0)
        codes = {issue["code"] for issue in validation["issues"]}
        self.assertIn("OCCUPANCY_MISSING", codes)

    def test_get_validation_ready_when_sections_complete(self):
        study = self._create_study()
        self._fill_required_sections(study)
        validation = study.get_validation()
        self.assertTrue(validation["ready"])
        self.assertEqual(validation["blocking_count"], 0)

    def test_get_validation_flags_unconfirmed_shading_and_estimated_provenance(self):
        study = self._create_study()
        self._fill_required_sections(study)
        self.env["greencube.cooling.shading"].create(
            {"study_id": study.id, "orientation": "west", "shading_type": "overhang", "confirmed": False}
        )
        study.equipment_load_ids.write({"provenance": "estimated_manual"})

        validation = study.get_validation()
        codes = {issue["code"] for issue in validation["issues"]}
        self.assertIn("SHADING_UNCONFIRMED", codes)
        self.assertIn("EQUIPMENT_ASSUMPTION", codes)
        # both are warnings, not blocking
        self.assertEqual(validation["blocking_count"], 0)
        self.assertTrue(validation["ready"])

    def test_action_confirm_assumptions_bulk_confirms_and_audits(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.equipment_load_ids.write({"provenance": "estimated_manual"})
        shading = self.env["greencube.cooling.shading"].create(
            {"study_id": study.id, "orientation": "west", "shading_type": "overhang", "confirmed": False}
        )

        count = study.action_confirm_assumptions()

        self.assertGreaterEqual(count, 2)
        self.assertEqual(study.equipment_load_ids.provenance, "user_confirmed")
        self.assertTrue(shading.confirmed)
        self.assertTrue(any("confirmée" in (m.body or "") for m in study.message_ids))

    # -- GC-COOLING-13: immutable calculation snapshot ---------------------

    def test_snapshot_is_immutable_and_superseded_on_recreate(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.action_create_snapshot()
        first_snapshot = study.active_snapshot_id
        self.assertEqual(first_snapshot.state, "frozen")

        with self.assertRaises(UserError):
            first_snapshot.write({"payload_json": "{}"})
        with self.assertRaises(UserError):
            first_snapshot.unlink()

        # Real input change since the first freeze -> recreate must
        # supersede the old snapshot with a genuinely new one.
        study.equipment_load_ids.write({"unit_power_w": 4500})
        study.action_create_snapshot()
        first_snapshot.invalidate_recordset()
        self.assertEqual(first_snapshot.state, "superseded")
        self.assertNotEqual(study.active_snapshot_id.id, first_snapshot.id)

    def test_recreate_snapshot_is_idempotent_when_nothing_changed(self):
        """GC-COOLING-13 'Idempotence': a double click, a network retry, or
        a refresh that calls action_create_snapshot() again before any
        study input actually changed must not freeze a second,
        functionally-identical snapshot superseding the first for no
        reason."""
        study = self._create_study()
        self._fill_required_sections(study)
        first_hash = study.action_create_snapshot()
        first_snapshot = study.active_snapshot_id

        second_hash = study.action_create_snapshot()

        self.assertEqual(first_hash, second_hash)
        first_snapshot.invalidate_recordset()
        self.assertEqual(first_snapshot.state, "frozen")
        self.assertEqual(study.active_snapshot_id.id, first_snapshot.id)
        self.assertEqual(len(study.snapshot_ids), 1)

    def test_action_calculate_uses_frozen_snapshot_not_live_data(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.action_create_snapshot()

        frozen_payload = json.loads(study.active_snapshot_id.payload_json)
        frozen_power = frozen_payload["equipment"][0]["unit_power_w"]
        self.assertEqual(frozen_power, 45.0)

        # Mutate equipment power AFTER the snapshot was frozen.
        study.equipment_load_ids.write({"unit_power_w": 4500})
        self.assertNotEqual(study.equipment_load_ids.unit_power_w, frozen_power)

        result = study.action_calculate()
        # The result must have been computed from the frozen (45 W) value,
        # not the mutated (4500 W) live value.
        result_payload = json.loads(study.active_snapshot_id.payload_json)
        self.assertEqual(result_payload["equipment"][0]["unit_power_w"], 45.0)
        self.assertTrue(result.exists())

    # -- GC-COOLING-10: usage/occupation schedule ------------------------

    def test_occupancy_schedule_computes_daily_hours_and_fraction(self):
        study = self._create_study()
        occupancy = self.env["greencube.cooling.occupancy.profile"].create(
            {
                "study_id": study.id,
                "usage_type": "office",
                "usual_occupants": 4,
                "maximum_occupants": 6,
                "start_hour": 8.0,
                "end_hour": 20.0,
            }
        )
        self.assertFalse(occupancy.crosses_midnight)
        self.assertEqual(occupancy.daily_occupied_hours, 12.0)
        self.assertAlmostEqual(occupancy.occupancy_fraction, 0.5)
        # Default weekly calendar matches the previous "Mon-Fri" default.
        self.assertEqual(occupancy.active_days_count, 5)
        self.assertTrue(occupancy.active_monday)
        self.assertFalse(occupancy.active_saturday)

    def test_occupancy_schedule_handles_midnight_crossing(self):
        study = self._create_study()
        occupancy = self.env["greencube.cooling.occupancy.profile"].create(
            {
                "study_id": study.id,
                "usage_type": "housing",
                "usual_occupants": 2,
                "maximum_occupants": 2,
                "start_hour": 22.0,
                "end_hour": 6.0,
            }
        )
        self.assertTrue(occupancy.crosses_midnight)
        self.assertEqual(occupancy.daily_occupied_hours, 8.0)
        self.assertAlmostEqual(occupancy.occupancy_fraction, 8.0 / 24.0)

    def test_occupancy_requires_at_least_one_active_day_when_occupied(self):
        study = self._create_study()
        with self.assertRaises(ValidationError):
            self.env["greencube.cooling.occupancy.profile"].create(
                {
                    "study_id": study.id,
                    "usage_type": "office",
                    "usual_occupants": 3,
                    "maximum_occupants": 3,
                    "active_monday": False,
                    "active_tuesday": False,
                    "active_wednesday": False,
                    "active_thursday": False,
                    "active_friday": False,
                    "active_saturday": False,
                    "active_sunday": False,
                }
            )
        # A profile with zero occupants (e.g. a technical/server room) is
        # allowed to have zero active days.
        empty_profile = self.env["greencube.cooling.occupancy.profile"].create(
            {
                "study_id": study.id,
                "usage_type": "server_room",
                "usual_occupants": 0,
                "maximum_occupants": 0,
                "active_monday": False,
                "active_tuesday": False,
                "active_wednesday": False,
                "active_thursday": False,
                "active_friday": False,
                "active_saturday": False,
                "active_sunday": False,
            }
        )
        self.assertEqual(empty_profile.active_days_count, 0)

    def test_occupancy_locked_once_study_validated(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.action_create_snapshot()
        study.action_calculate()
        study.action_validate()

        occupancy = study.occupancy_profile_ids[:1]
        with self.assertRaises(UserError):
            occupancy.write({"usual_occupants": 9})
        with self.assertRaises(UserError):
            occupancy.unlink()
        # provenance-only writes (bulk-confirm) remain allowed post-validation.
        occupancy.write({"provenance": "user_confirmed"})

        # A revision copies the sub-line via copy(), never write()/unlink()
        # on the validated original, so it must still succeed.
        action = study.action_create_revision()
        revision = self.env["greencube.cooling.study"].browse(action["res_id"])
        self.assertEqual(len(revision.occupancy_profile_ids), 1)
        # The copy is a fresh record on a draft study: fully editable.
        revision.occupancy_profile_ids.write({"usual_occupants": 3, "maximum_occupants": 3})
        self.assertEqual(revision.occupancy_profile_ids.usual_occupants, 3)

    def test_occupancy_fraction_feeds_mercure_input_not_hardcoded(self):
        """GC-COOLING-10 core fix: the occupancy schedule must actually
        change the sensible/latent gains MERCURE computes, not just be
        displayed and silently ignored."""
        study = self._create_study()
        self._fill_required_sections(study)
        occupancy = study.occupancy_profile_ids[:1]
        occupancy.write({"start_hour": 8.0, "end_hour": 20.0})  # 12h -> fraction 0.5
        study.action_create_snapshot()

        payload = json.loads(study.active_snapshot_id.payload_json)
        self.assertAlmostEqual(payload["occupancy"]["occupancy_fraction"], 0.5)

    # -- ventilation / infiltration (GC-COOLING-12) ----------------------

    def test_ventilation_profile_locked_once_study_validated(self):
        study = self._create_study()
        self._fill_required_sections(study)
        study.action_create_snapshot()
        study.action_calculate()
        study.action_validate()

        ventilation = study.ventilation_profile_ids[:1]
        with self.assertRaises(UserError):
            ventilation.write({"airflow_m3h": 999})
        with self.assertRaises(UserError):
            ventilation.unlink()
        # provenance-only writes remain allowed post-validation.
        ventilation.write({"provenance": "user_confirmed"})

    def test_effective_infiltration_prefers_n50_over_manual_ach(self):
        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]
        ventilation.write(
            {
                "airtightness_n50": 6.0,
                "wind_exposure": "normal",
                "infiltration_ach": 0.6,
                "door_opening_frequency": "rare",
                "window_opening_frequency": "rare",
            }
        )
        # n50 / 20 (normal shielding) = 0.3, not the manually entered 0.6.
        self.assertAlmostEqual(ventilation.get_effective_infiltration_ach(), 0.3)

    def test_effective_infiltration_falls_back_to_manual_ach_without_n50(self):
        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]
        ventilation.write(
            {"airtightness_n50": 0.0, "infiltration_ach": 0.6, "door_opening_frequency": "rare", "window_opening_frequency": "rare"}
        )
        self.assertAlmostEqual(ventilation.get_effective_infiltration_ach(), 0.6)

    def test_door_and_window_opening_increase_infiltration_monotonically(self):
        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]
        ventilation.write({"airtightness_n50": 0.0, "infiltration_ach": 0.5})

        ventilation.write({"door_opening_frequency": "rare", "window_opening_frequency": "rare"})
        rare = ventilation.get_effective_infiltration_ach()
        ventilation.write({"door_opening_frequency": "frequent", "window_opening_frequency": "frequent"})
        frequent = ventilation.get_effective_infiltration_ach()
        ventilation.write({"door_opening_frequency": "continuous", "window_opening_frequency": "continuous"})
        continuous = ventilation.get_effective_infiltration_ach()

        self.assertLess(rare, frequent)
        self.assertLess(frequent, continuous)

    def test_effective_infiltration_feeds_mercure_input_not_ignored(self):
        """GC-COOLING-12 core fix: n50 and door/window opening frequency were
        stored and exposed via the API but had zero effect on the solver
        input. Door/window opening was ignored entirely."""
        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]
        ventilation.write(
            {
                "airtightness_n50": 6.0,
                "wind_exposure": "normal",
                "door_opening_frequency": "continuous",
                "window_opening_frequency": "continuous",
            }
        )
        study.action_create_snapshot()
        payload = json.loads(study.active_snapshot_id.payload_json)
        # 0.3 (n50/20) + 0.15 + 0.15 (continuous door + window increments)
        self.assertAlmostEqual(payload["infiltration"]["air_changes_per_hour"], 0.6)

    def test_higher_infiltration_never_decreases_ventilation_load(self):
        """Monotonicity per README_GC-COOLING-12: more infiltration must
        never reduce the outdoor-air sensible load."""
        from ..services.mercure.engine import run_mercure

        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]

        ventilation.write({"airtightness_n50": 0.0, "infiltration_ach": 0.2})
        low_result = run_mercure(study._build_mercure_input())
        low_scenario = next(s for s in low_result.scenario_results if s.scenario_code == "reference_summer")

        ventilation.write({"airtightness_n50": 0.0, "infiltration_ach": 2.0})
        high_result = run_mercure(study._build_mercure_input())
        high_scenario = next(s for s in high_result.scenario_results if s.scenario_code == "reference_summer")

        self.assertLessEqual(low_scenario.sensible_load_w, high_scenario.sensible_load_w)

    def test_fan_fraction_dissipated_in_zone_is_not_hardcoded(self):
        """GC-COOLING-14: fan_fraction_dissipated_in_zone used to be
        hardcoded to 1.0 in _build_mercure_input regardless of the
        ventilation profile; it must now be read from the profile."""
        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]
        ventilation.write({"fan_fraction_dissipated_in_zone": 0.4})
        payload = study._build_mercure_input()
        self.assertAlmostEqual(payload.ventilation.fan_fraction_dissipated_in_zone, 0.4)

    def test_fan_heat_gain_reflects_dissipation_fraction(self):
        """A lower fan_fraction_dissipated_in_zone must strictly reduce the
        fan_heat breakdown entry (fan not fully inside the cooled zone)."""
        from ..services.mercure.engine import run_mercure

        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]
        ventilation.write({"fan_power_w": 100, "fan_fraction_dissipated_in_zone": 1.0})
        full_result = run_mercure(study._build_mercure_input())
        full_scenario = full_result.scenario_results[0]
        full_fan = next(e.total_w for e in full_scenario.breakdown if e.component_code == "fan_heat")

        ventilation.write({"fan_fraction_dissipated_in_zone": 0.2})
        partial_result = run_mercure(study._build_mercure_input())
        partial_scenario = partial_result.scenario_results[0]
        partial_fan = next(e.total_w for e in partial_scenario.breakdown if e.component_code == "fan_heat")

        self.assertLess(partial_fan, full_fan)

    def test_infiltration_method_is_ach_when_no_n50_measured(self):
        """GC-COOLING-14: the method label used to be hardcoded to
        'n50_estimated' even when the infiltration rate came from a plain
        manually-entered infiltration_ach (airtightness_n50 == 0), which
        wrongly fired LOW_CONFIDENCE_INFILTRATION and penalized the
        confidence score for data that was not actually an n50 estimate."""
        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]
        ventilation.write({"airtightness_n50": 0.0, "infiltration_ach": 0.6})
        payload = study._build_mercure_input()
        self.assertEqual(payload.infiltration.method, "ach")

    def test_infiltration_method_is_n50_estimated_when_n50_measured(self):
        study = self._create_study()
        self._fill_required_sections(study)
        ventilation = study.ventilation_profile_ids[:1]
        ventilation.write({"airtightness_n50": 6.0, "wind_exposure": "normal"})
        payload = study._build_mercure_input()
        self.assertEqual(payload.infiltration.method, "n50_estimated")


@tagged("post_install", "-at_install")
class TestCoolingStudySecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref("greencube_cooling.group_greencube_cooling_user")
        cls.group_technician = cls.env.ref("greencube_cooling.group_greencube_cooling_technician")
        cls.group_manager = cls.env.ref("greencube_cooling.group_greencube_cooling_manager")
        # A real HTTP caller of this module is always an Odoo internal user
        # (see tests/test_api_security.py, tests/test_http_api.py, which
        # both add this group explicitly). user_a needs it here too, since
        # test_user_can_create_and_modify_own_private_spec_and_children
        # creates a mail.thread-inherited record (thermal.specification) as
        # user_a: mail's follower/subtype bootstrap requires base.group_user,
        # independent of the greencube-specific ir.rule/ACL under test.
        cls.group_internal_user = cls.env.ref("base.group_user")

        cls.company_a = cls.env["res.company"].create({"name": "GreenCube Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "GreenCube Company B"})

        cls.user_a = cls.env["res.users"].create(
            {
                "name": "User A",
                "login": "gc_user_a@example.com",
                "email": "gc_user_a@example.com",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
                "groups_id": [(6, 0, [cls.group_user.id, cls.group_internal_user.id])],
            }
        )
        cls.user_b = cls.env["res.users"].create(
            {
                "name": "User B",
                "login": "gc_user_b@example.com",
                "email": "gc_user_b@example.com",
                "company_id": cls.company_b.id,
                "company_ids": [(6, 0, [cls.company_b.id])],
                "groups_id": [(6, 0, [cls.group_user.id])],
            }
        )
        cls.technician_a = cls.env["res.users"].create(
            {
                "name": "Technician A",
                "login": "gc_tech_a@example.com",
                "email": "gc_tech_a@example.com",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
                "groups_id": [(6, 0, [cls.group_technician.id])],
            }
        )
        # Second standard user in the SAME company as user_a: needed to test
        # ownership isolation independently of company isolation (a plain
        # User must not see another user's objects even within one company).
        cls.user_a2 = cls.env["res.users"].create(
            {
                "name": "User A2",
                "login": "gc_user_a2@example.com",
                "email": "gc_user_a2@example.com",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
                "groups_id": [(6, 0, [cls.group_user.id])],
            }
        )
        cls.manager = cls.env["res.users"].create(
            {
                "name": "Manager A",
                "login": "gc_mgr_a@example.com",
                "email": "gc_mgr_a@example.com",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
                "groups_id": [(6, 0, [cls.group_manager.id])],
            }
        )

        cls.spec_a = cls.env["greencube.thermal.specification"].with_company(cls.company_a).create(
            _thermal_spec_vals(company_id=cls.company_a.id, code="GC-A")
        )
        cls.spec_b = cls.env["greencube.thermal.specification"].with_company(cls.company_b).create(
            _thermal_spec_vals(company_id=cls.company_b.id, code="GC-B")
        )

        cls.study_a_by_user_a = cls.env["greencube.cooling.study"].create(
            {
                "name": "Study A (user A)",
                "company_id": cls.company_a.id,
                "user_id": cls.user_a.id,
                "thermal_specification_id": cls.spec_a.id,
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
            }
        )
        cls.study_a_by_technician = cls.env["greencube.cooling.study"].create(
            {
                "name": "Study A (technician)",
                "company_id": cls.company_a.id,
                "user_id": cls.technician_a.id,
                "thermal_specification_id": cls.spec_a.id,
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
            }
        )
        cls.study_b_by_user_b = cls.env["greencube.cooling.study"].create(
            {
                "name": "Study B (user B)",
                "company_id": cls.company_b.id,
                "user_id": cls.user_b.id,
                "thermal_specification_id": cls.spec_b.id,
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
            }
        )

    def test_user_sees_only_own_studies(self):
        studies = self.env["greencube.cooling.study"].with_user(self.user_a).search([])
        self.assertIn(self.study_a_by_user_a, studies)
        self.assertNotIn(self.study_a_by_technician, studies)
        self.assertNotIn(self.study_b_by_user_b, studies)

    def test_user_of_company_a_cannot_read_company_b_study(self):
        with self.assertRaises(AccessError):
            self.study_b_by_user_b.with_user(self.user_a).read(["name"])

    def test_plain_user_cannot_validate(self):
        study = self.study_a_by_user_a.with_user(self.user_a)
        self.env["greencube.cooling.occupancy.profile"].create(
            {"study_id": study.id, "usage_type": "housing", "usual_occupants": 1, "maximum_occupants": 1}
        )
        study.sudo().action_create_snapshot()
        study.sudo().action_calculate()
        with self.assertRaises(UserError):
            study.action_validate()

    def test_technician_sees_all_company_studies(self):
        studies = self.env["greencube.cooling.study"].with_user(self.technician_a).search([])
        self.assertIn(self.study_a_by_user_a, studies)
        self.assertIn(self.study_a_by_technician, studies)
        self.assertNotIn(self.study_b_by_user_b, studies)

    def test_plain_user_cannot_write_result(self):
        result = self.env["greencube.cooling.result"].sudo().create(
            {
                "study_id": self.study_a_by_user_a.id,
                "state": "success",
                "recommended_capacity_w": 1000,
            }
        )
        with self.assertRaises(AccessError):
            result.with_user(self.user_a).write({"state": "superseded"})

    # -- GC-COOLING-01: private spec + children owned/created by a plain User --

    def test_user_can_create_and_modify_own_private_spec_and_children(self):
        """The wizard's PUT /thermal-specification, PUT /occupancy-profile,
        etc. run as the plain User (no sudo()). A private (standard_model
        False) specification and its children, on a study the User owns,
        must be creatable/writable without AccessError."""
        # Study creation itself goes through ir.sequence.next_by_code(),
        # gated on base.group_user ("Internal User") which these
        # greencube-only test fixtures don't carry (unlike a real HTTP
        # caller, who always is an internal user) — created via sudo() like
        # the other fixtures in this class, so the test isolates what
        # GC-COOLING-01 actually requires: spec/facade/occupancy writes as
        # a plain User on their own draft study.
        study = self.env["greencube.cooling.study"].sudo().create(
            {
                "name": "User A private study",
                "company_id": self.company_a.id,
                "user_id": self.user_a.id,
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
            }
        )
        Spec = self.env["greencube.thermal.specification"].with_user(self.user_a)
        private_spec = Spec.create(
            _thermal_spec_vals(company_id=self.company_a.id, code="GC-A-PRIVATE") | {"standard_model": False}
        )
        private_spec.write({"notes": "<p>édité par user A</p>"})
        self.env["greencube.thermal.facade"].with_user(self.user_a).create(
            {
                "thermal_specification_id": private_spec.id,
                "orientation": "south",
                "gross_area_m2": 10.0,
                "glazing_area_m2": 4.0,
            }
        )
        study.with_user(self.user_a).write({"thermal_specification_id": private_spec.id})
        self.env["greencube.cooling.occupancy.profile"].with_user(self.user_a).create(
            {"study_id": study.id, "usage_type": "housing", "usual_occupants": 2, "maximum_occupants": 3}
        )
        self.assertEqual(study.user_id, self.user_a)
        self.assertEqual(private_spec.standard_model, False)

    def test_manager_cannot_create_private_spec_shortcut_but_can_edit_catalog(self):
        # Manager manages the standard catalog (standard_model=True), which
        # the plain User cannot touch.
        catalog_spec = self.spec_a.with_user(self.manager)
        catalog_spec.write({"notes": "<p>mis à jour par le manager</p>"})
        with self.assertRaises(AccessError):
            self.spec_a.with_user(self.user_a).write({"notes": "<p>user ne peut pas</p>"})

    # -- GC-COOLING-01: ownership isolation WITHIN the same company --------

    def test_user_a_cannot_read_or_write_user_a2_child_objects(self):
        study_a2 = self.env["greencube.cooling.study"].sudo().create(
            {
                "name": "Study A2 (user A2)",
                "company_id": self.company_a.id,
                "user_id": self.user_a2.id,
                "thermal_specification_id": self.spec_a.id,
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
            }
        )
        occupancy_a2 = self.env["greencube.cooling.occupancy.profile"].sudo().create(
            {"study_id": study_a2.id, "usage_type": "housing", "usual_occupants": 2, "maximum_occupants": 3}
        )
        equipment_a2 = self.env["greencube.cooling.equipment.load"].sudo().create(
            {
                "study_id": study_a2.id,
                "name": "Serveur",
                "category": "it",
                "quantity": 1,
                "unit_power_w": 100,
                "usage_hours_per_day": 24,
                "simultaneity_percent": 100,
            }
        )
        with self.assertRaises(AccessError):
            study_a2.with_user(self.user_a).read(["name"])
        with self.assertRaises(AccessError):
            occupancy_a2.with_user(self.user_a).read(["usual_occupants"])
        with self.assertRaises(AccessError):
            equipment_a2.with_user(self.user_a).write({"unit_power_w": 1})
        # user_a2 is unaffected and can operate on their own objects.
        occupancy_a2.with_user(self.user_a2).write({"usual_occupants": 3})
        self.assertEqual(occupancy_a2.usual_occupants, 3)

    # -- GC-COOLING-01: manager manages standards without owning private studies --

    def test_manager_can_manage_company_studies_without_becoming_owner(self):
        study = self.study_a_by_user_a.with_user(self.manager)
        # Manager (implies technician) can see and act on the study...
        study.write({"notes": "<p>Revue par le manager.</p>"})
        # ...but does not silently become its owner.
        self.assertEqual(self.study_a_by_user_a.user_id, self.user_a)
        self.assertIn("Revue", self.study_a_by_user_a.notes)

    def test_manager_cannot_access_company_b_objects(self):
        with self.assertRaises(AccessError):
            self.study_b_by_user_b.with_user(self.manager).read(["name"])

    # -- GC-COOLING-01: validated equipment selection is immutable --------

    def test_validated_equipment_selection_is_immutable(self):
        result = self.env["greencube.cooling.result"].sudo().create(
            {"study_id": self.study_a_by_user_a.id, "state": "success", "recommended_capacity_w": 3500}
        )
        product = self.env["product.product"].sudo().create({"name": "Split GC-3500"})
        selection = self.env["greencube.cooling.equipment.selection"].sudo().create(
            {
                "study_id": self.study_a_by_user_a.id,
                "result_id": result.id,
                "product_id": product.id,
                "compatibility_status": "recommended",
                "company_id": self.company_a.id,
                "state": "selected",
            }
        )
        # Not yet validated: still editable.
        selection.write({"price": 1200.0})

        selection.write({"state": "validated"})
        with self.assertRaises(UserError):
            selection.write({"price": 999.0})
        with self.assertRaises(UserError):
            selection.unlink()

    # -- GC-COOLING-18: action_validate() is the only path to "validated" --

    def test_action_validate_only_from_selected_state(self):
        result = self.env["greencube.cooling.result"].sudo().create(
            {"study_id": self.study_a_by_user_a.id, "state": "success", "recommended_capacity_w": 3500}
        )
        product = self.env["product.product"].sudo().create({"name": "Split GC-3500"})
        selection = self.env["greencube.cooling.equipment.selection"].sudo().create(
            {
                "study_id": self.study_a_by_user_a.id,
                "result_id": result.id,
                "product_id": product.id,
                "compatibility_status": "recommended",
                "company_id": self.company_a.id,
                "state": "selected",
            }
        )
        selection.action_validate()
        self.assertEqual(selection.state, "validated")
        self.assertTrue(selection.validated_at)
        self.assertEqual(selection.validator_id, self.env.user)
        # Validating again (already validated) is refused, not a silent no-op.
        with self.assertRaises(UserError):
            selection.action_validate()

    def test_supersede_links_to_previous_selection_without_deleting_it(self):
        result = self.env["greencube.cooling.result"].sudo().create(
            {"study_id": self.study_a_by_user_a.id, "state": "success", "recommended_capacity_w": 3500}
        )
        product_1 = self.env["product.product"].sudo().create({"name": "Split GC-3500 A"})
        product_2 = self.env["product.product"].sudo().create({"name": "Split GC-3500 B"})
        first = self.env["greencube.cooling.equipment.selection"].sudo().create(
            {
                "study_id": self.study_a_by_user_a.id,
                "result_id": result.id,
                "product_id": product_1.id,
                "compatibility_status": "recommended",
                "company_id": self.company_a.id,
                "state": "selected",
            }
        )
        first.write({"state": "superseded"})
        second = self.env["greencube.cooling.equipment.selection"].sudo().create(
            {
                "study_id": self.study_a_by_user_a.id,
                "result_id": result.id,
                "product_id": product_2.id,
                "compatibility_status": "recommended",
                "company_id": self.company_a.id,
                "state": "selected",
                "supersedes_id": first.id,
            }
        )
        self.assertEqual(second.supersedes_id, first)
        # The superseded record still exists, untouched history.
        self.assertTrue(first.exists())
        self.assertEqual(first.state, "superseded")

    def test_deleting_study_with_validated_selection_is_blocked(self):
        """GC-COOLING-18 audit finding: `study_id` on equipment.selection
        carries ondelete="cascade", which Postgres enforces as a raw SQL
        constraint and bypasses equipment.selection.unlink()'s own guard.
        The guard must therefore also live on cooling.study.unlink()."""
        study = self.env["greencube.cooling.study"].sudo().create(
            {
                "name": "Study to be deleted",
                "company_id": self.company_a.id,
                "user_id": self.user_a.id,
                "thermal_specification_id": self.spec_a.id,
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
            }
        )
        result = self.env["greencube.cooling.result"].sudo().create(
            {"study_id": study.id, "state": "success", "recommended_capacity_w": 3500}
        )
        product = self.env["product.product"].sudo().create({"name": "Split GC-3500 (to validate)"})
        selection = self.env["greencube.cooling.equipment.selection"].sudo().create(
            {
                "study_id": study.id,
                "result_id": result.id,
                "product_id": product.id,
                "compatibility_status": "recommended",
                "company_id": self.company_a.id,
                "state": "selected",
            }
        )
        selection.action_validate()
        with self.assertRaises(UserError):
            study.sudo().unlink()
        self.assertTrue(selection.exists())

    def test_product_price_change_after_validation_does_not_alter_history(self):
        result = self.env["greencube.cooling.result"].sudo().create(
            {"study_id": self.study_a_by_user_a.id, "state": "success", "recommended_capacity_w": 3500}
        )
        product = self.env["product.product"].sudo().create({"name": "Split GC-3500", "list_price": 1200.0})
        selection = self.env["greencube.cooling.equipment.selection"].sudo().create(
            {
                "study_id": self.study_a_by_user_a.id,
                "result_id": result.id,
                "product_id": product.id,
                "compatibility_status": "recommended",
                "company_id": self.company_a.id,
                "state": "selected",
                "price": product.list_price,
                "product_name": product.name,
                "nominal_capacity_w": 3500,
            }
        )
        selection.action_validate()

        # Catalog moves on: price changes and the product gets archived.
        product.write({"list_price": 1600.0, "active": False})

        self.assertEqual(selection.price, 1200.0)
        self.assertEqual(selection.product_name, "Split GC-3500")
        self.assertEqual(selection.nominal_capacity_w, 3500)

    # -- GC-COOLING-18: equipment_selection was missing a per-user IDOR ---
    # -- rule (only company-scoped); a plain User in the same company ----
    # -- could read/write another user's equipment selection. -------------

    def test_user_a_cannot_read_user_a2_equipment_selection(self):
        study_a2 = self.env["greencube.cooling.study"].sudo().create(
            {
                "name": "Study A2 for equipment selection IDOR",
                "company_id": self.company_a.id,
                "user_id": self.user_a2.id,
                "thermal_specification_id": self.spec_a.id,
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
            }
        )
        result_a2 = self.env["greencube.cooling.result"].sudo().create(
            {"study_id": study_a2.id, "state": "success", "recommended_capacity_w": 3500}
        )
        product = self.env["product.product"].sudo().create({"name": "Split GC-3500 (A2)"})
        selection_a2 = self.env["greencube.cooling.equipment.selection"].sudo().create(
            {
                "study_id": study_a2.id,
                "result_id": result_a2.id,
                "product_id": product.id,
                "compatibility_status": "recommended",
                "company_id": self.company_a.id,
                "state": "selected",
            }
        )
        with self.assertRaises(AccessError):
            selection_a2.with_user(self.user_a).read(["state"])
        with self.assertRaises(AccessError):
            selection_a2.with_user(self.user_a).write({"price": 1.0})
        # A technician (broader company-wide access) is unaffected.
        self.assertEqual(
            selection_a2.with_user(self.technician_a).state, "selected"
        )

    # -- GC-COOLING-01 §16.3: a used solver version cannot be deleted -----

    def test_used_solver_version_cannot_be_deleted(self):
        solver_version = self.env["greencube.cooling.solver.version"].sudo().create(
            {"name": "MERCURE test", "code": "MERCURE-TEST", "version": "9.9.9", "state": "active"}
        )
        self.env["greencube.cooling.result"].sudo().create(
            {
                "study_id": self.study_a_by_user_a.id,
                "state": "success",
                "recommended_capacity_w": 1000,
                "solver_version_id": solver_version.id,
            }
        )
        with self.assertRaises(UserError):
            solver_version.unlink()
