# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class GreencubeCoolingSimulationArtifact(models.Model):
    """A reference to a file produced while processing a calculation job
    (GC-COOLING-15 pt.1/pt.3): Honeybee model JSON, EPW weather file, IDF,
    EnergyPlus SQL output, or a run log. The actual bytes live in a normal
    `ir.attachment` (Odoo's own file storage, not a bespoke Binary field
    directly on this model) — this record is only the typed, checksummed,
    immutable pointer to it."""

    _name = "greencube.cooling.simulation.artifact"
    _description = "GreenCube Cooling Simulation Artifact"
    _order = "create_date desc"

    job_id = fields.Many2one("greencube.cooling.calculation.job", required=True, ondelete="cascade", index=True)
    artifact_type = fields.Selection(
        [
            ("honeybee_json", "Honeybee model (JSON)"),
            ("epw", "Weather file (EPW)"),
            ("idf", "EnergyPlus input (IDF)"),
            ("sql", "EnergyPlus output (SQL)"),
            ("log", "Simulation log"),
        ],
        required=True,
    )
    checksum_sha256 = fields.Char(required=True, index=True)
    attachment_id = fields.Many2one("ir.attachment", required=True, ondelete="restrict")

    def write(self, vals):
        raise UserError("A simulation artifact is immutable once created.")

    def unlink(self):
        raise UserError("A simulation artifact cannot be deleted.")
