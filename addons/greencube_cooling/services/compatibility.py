# -*- coding: utf-8 -*-
"""Equipment compatibility engine.

Pure function of (product technical data, governing result) -> assessment.
Mirrors frontend/src/equipment/compatibility.ts so both layers agree on the
same rules until the frontend is fully backed by this API.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ProductTechnicalData:
    capacity_at_45c_w: float
    max_outdoor_temperature_c: float
    shr: float


@dataclass
class CompatibilityAssessment:
    status: str
    reasons: List[str] = field(default_factory=list)
    capacity_at_design_condition_w: float = 0.0
    oversizing_ratio: float = 0.0


def assess_compatibility(product: ProductTechnicalData, recommended_load_w: float, governing_shr: float) -> CompatibilityAssessment:
    reasons: List[str] = []
    capacity_at_design_condition_w = product.capacity_at_45c_w
    oversizing_ratio = (capacity_at_design_condition_w / recommended_load_w) if recommended_load_w > 0 else 0.0

    if capacity_at_design_condition_w < recommended_load_w * 0.9:
        reasons.append("Capacité insuffisante à la température de calcul.")
        return CompatibilityAssessment("incompatible", reasons, capacity_at_design_condition_w, oversizing_ratio)

    if product.max_outdoor_temperature_c < 40:
        reasons.append("Plage de température extérieure maximale insuffisante pour un scénario canicule.")
        return CompatibilityAssessment("incompatible", reasons, capacity_at_design_condition_w, oversizing_ratio)

    if oversizing_ratio > 2.2:
        reasons.append("Surdimensionnement important : modulation et confort peuvent être dégradés.")
        return CompatibilityAssessment("not_recommended", reasons, capacity_at_design_condition_w, oversizing_ratio)

    shr_gap = abs(product.shr - governing_shr)
    if shr_gap > 0.15:
        reasons.append("Écart notable entre le SHR produit et le SHR du besoin : vérifier la déshumidification.")
        return CompatibilityAssessment("compatible_with_conditions", reasons, capacity_at_design_condition_w, oversizing_ratio)

    if 1 <= oversizing_ratio <= 1.3:
        reasons.append("Capacité bien ajustée au besoin recommandé, y compris à haute température.")
        return CompatibilityAssessment("recommended", reasons, capacity_at_design_condition_w, oversizing_ratio)

    if 1.3 < oversizing_ratio <= 1.6:
        reasons.append("Marge confortable, bonne alternative si le modèle recommandé est indisponible.")
        return CompatibilityAssessment("strong_alternative", reasons, capacity_at_design_condition_w, oversizing_ratio)

    reasons.append("Compatible mais avec une marge de dimensionnement plus large que l'optimum.")
    return CompatibilityAssessment("compatible", reasons, capacity_at_design_condition_w, oversizing_ratio)
