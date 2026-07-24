# -*- coding: utf-8 -*-
"""Equipment compatibility engine.

Pure function of (product technical data, governing result) -> assessment.
Mirrors frontend/src/equipment/compatibility.ts so both layers agree on the
same rules until the frontend is fully backed by this API.
"""
from dataclasses import dataclass, field
from typing import List, Optional

# Recommendation categories, from best to worst. Used both to label a
# result and, critically, to *rank* recommendations: sorting must never
# degrade to a raw ascending sort on `oversizing_ratio` alone (GC-COOLING-18
# audit finding), because a product with missing/zero technical data ends
# up with oversizing_ratio == 0.0 and would otherwise float to the very top
# of the list ahead of every genuinely well-matched product.
STATUS_RANK = {
    "recommended": 0,
    "strong_alternative": 1,
    "compatible": 2,
    "compatible_with_conditions": 3,
    "not_recommended": 4,
    "insufficient_data": 5,
    "incompatible": 6,
}


@dataclass(frozen=True)
class ProductTechnicalData:
    # None (or a non-positive value) means "not provided by the catalog
    # entry", distinct from a genuine, very small capacity. A real cooling
    # unit never has zero rated capacity, so treating 0/None as "missing"
    # rather than "0 W of cooling" is deliberate.
    capacity_at_45c_w: Optional[float]
    max_outdoor_temperature_c: Optional[float]
    shr: Optional[float]


@dataclass
class CompatibilityAssessment:
    status: str
    reasons: List[str] = field(default_factory=list)
    capacity_at_design_condition_w: float = 0.0
    oversizing_ratio: Optional[float] = None
    missing_fields: List[str] = field(default_factory=list)


def _is_missing(value: Optional[float]) -> bool:
    return value is None or value <= 0


def assess_compatibility(product: ProductTechnicalData, recommended_load_w: float, governing_shr: float) -> CompatibilityAssessment:
    reasons: List[str] = []
    missing_fields: List[str] = []

    if _is_missing(product.capacity_at_45c_w):
        missing_fields.append("capacity_at_45c_w")
    if _is_missing(product.max_outdoor_temperature_c):
        missing_fields.append("max_outdoor_temperature_c")
    if product.shr is None:
        missing_fields.append("shr")

    if missing_fields:
        reasons.append(
            "Données techniques insuffisantes pour évaluer la compatibilité : "
            + ", ".join(missing_fields) + "."
        )
        return CompatibilityAssessment("insufficient_data", reasons, 0.0, None, missing_fields)

    capacity_at_design_condition_w = product.capacity_at_45c_w
    oversizing_ratio = (capacity_at_design_condition_w / recommended_load_w) if recommended_load_w > 0 else None

    if oversizing_ratio is None:
        reasons.append("Puissance recommandée du résultat thermique indisponible ou nulle.")
        return CompatibilityAssessment("insufficient_data", reasons, capacity_at_design_condition_w, None, ["recommended_load_w"])

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


def recommendation_sort_key(assessment: CompatibilityAssessment, tie_breaker):
    """Stable, missing-data-robust ordering for a list of recommendations.

    Primary key: status category (recommended first, incompatible last).
    Secondary key: closeness of oversizing_ratio to the ideal value of 1.0
    (a missing ratio sorts after every product that has one, within the
    same status). Tertiary key: caller-supplied tie breaker (e.g. product
    id) so equal-rank products always come back in a deterministic order
    instead of depending on dict/list iteration order.
    """
    status_rank = STATUS_RANK.get(assessment.status, len(STATUS_RANK))
    if assessment.oversizing_ratio is None:
        proximity = float("inf")
    else:
        proximity = abs(assessment.oversizing_ratio - 1.0)
    return (status_rank, proximity, tie_breaker)
