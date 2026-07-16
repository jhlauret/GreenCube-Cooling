import type { CatalogProduct } from '../api/mockCatalog';
import type { MercureScenarioResult } from '../mercure/types';

export type CompatibilityStatus =
  | 'recommended'
  | 'strong_alternative'
  | 'compatible'
  | 'compatible_with_conditions'
  | 'not_recommended'
  | 'incompatible'
  | 'insufficient_data';

export interface CompatibilityAssessment {
  status: CompatibilityStatus;
  reasons: string[];
  capacityAtDesignConditionW: number;
  oversizingRatio: number;
}

export function assessCompatibility(product: CatalogProduct, governing: MercureScenarioResult): CompatibilityAssessment {
  const reasons: string[] = [];
  const capacityAtDesignConditionW = product.capacityAt45CW;
  const oversizingRatio = capacityAtDesignConditionW / governing.recommendedLoadW;

  if (capacityAtDesignConditionW < governing.recommendedLoadW * 0.9) {
    reasons.push('Capacité insuffisante à la température de calcul.');
    return { status: 'incompatible', reasons, capacityAtDesignConditionW, oversizingRatio };
  }

  if (product.maxOutdoorTemperatureC < 40) {
    reasons.push('Plage de température extérieure maximale insuffisante pour un scénario canicule.');
    return { status: 'incompatible', reasons, capacityAtDesignConditionW, oversizingRatio };
  }

  if (oversizingRatio > 2.2) {
    reasons.push('Surdimensionnement important : modulation et confort peuvent être dégradés.');
    return { status: 'not_recommended', reasons, capacityAtDesignConditionW, oversizingRatio };
  }

  const shrGap = Math.abs(product.shr - governing.shr);
  if (shrGap > 0.15) {
    reasons.push('Écart notable entre le SHR produit et le SHR du besoin : vérifier la déshumidification.');
    return { status: 'compatible_with_conditions', reasons, capacityAtDesignConditionW, oversizingRatio };
  }

  if (oversizingRatio >= 1 && oversizingRatio <= 1.3) {
    reasons.push('Capacité bien ajustée au besoin recommandé, y compris à haute température.');
    return { status: 'recommended', reasons, capacityAtDesignConditionW, oversizingRatio };
  }

  if (oversizingRatio > 1.3 && oversizingRatio <= 1.6) {
    reasons.push('Marge confortable, bonne alternative si le modèle recommandé est indisponible.');
    return { status: 'strong_alternative', reasons, capacityAtDesignConditionW, oversizingRatio };
  }

  reasons.push('Compatible mais avec une marge de dimensionnement plus large que l\'optimum.');
  return { status: 'compatible', reasons, capacityAtDesignConditionW, oversizingRatio };
}

export const COMPATIBILITY_LABELS: Record<CompatibilityStatus, string> = {
  recommended: 'Recommandé',
  strong_alternative: 'Alternative solide',
  compatible: 'Compatible',
  compatible_with_conditions: 'Compatible sous conditions',
  not_recommended: 'Non recommandé',
  incompatible: 'Incompatible',
  insufficient_data: 'Données insuffisantes',
};

export const COMPATIBILITY_TONE: Record<CompatibilityStatus, 'brand' | 'warn' | 'danger' | 'neutral'> = {
  recommended: 'brand',
  strong_alternative: 'brand',
  compatible: 'neutral',
  compatible_with_conditions: 'warn',
  not_recommended: 'warn',
  incompatible: 'danger',
  insufficient_data: 'neutral',
};
