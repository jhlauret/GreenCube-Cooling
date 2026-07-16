# -*- coding: utf-8 -*-
"""TransactionCase tests exercising the module through the real Odoo ORM.

These complement tests/test_mercure_engine.py and tests/test_compatibility.py
(pure-Python, ORM-independent) by covering the parts of GC-COOLING-01 §27
that only make sense against a live registry: status cycle, revision
locking, result/component immutability, multi-company ACL/record rules and
action_calculate() end-to-end.
"""
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


@tagged("post_install", "-at_install")
class TestCoolingStudySecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref("greencube_cooling.group_greencube_cooling_user")
        cls.group_technician = cls.env.ref("greencube_cooling.group_greencube_cooling_technician")

        cls.company_a = cls.env["res.company"].create({"name": "GreenCube Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "GreenCube Company B"})

        cls.user_a = cls.env["res.users"].create(
            {
                "name": "User A",
                "login": "gc_user_a@example.com",
                "email": "gc_user_a@example.com",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
                "groups_id": [(6, 0, [cls.group_user.id])],
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
