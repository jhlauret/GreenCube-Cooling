import { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { WizardFooter } from '../../components/layout/WizardFooter';
import { useWizardNav } from '../useWizardNav';
import { useStudyStore } from '../../store/studyStore';
import type { EquipmentItem, StudyDraft } from '../../types/study';
import { fetchInternalLoadsCatalog, type InternalLoadCatalogEntry } from '../../equipment/internalLoadsCatalog';
import { defaultNextSteps } from './defaultNextSteps';

function simultaneousPowerW(item: EquipmentItem): number {
  return item.quantity * item.unitPowerW * (item.simultaneityPercent / 100);
}

export function EquipmentStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const updateStudy = useStudyStore((state) => state.updateStudy);
  const { studyId, goToNext, goToPrevious } = useWizardNav('equipment');

  // Internal-loads catalog fetched from Odoo (GC-COOLING-11) — never
  // hardcoded in the frontend. `product.template` records flagged
  // `is_internal_load_equipment` are the sole source of these templates.
  const [catalog, setCatalog] = useState<InternalLoadCatalogEntry[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchInternalLoadsCatalog()
      .then((data) => {
        if (!cancelled) setCatalog(data);
      })
      .catch((err) => {
        if (!cancelled) setCatalogError(err instanceof Error ? err.message : 'Impossible de charger le catalogue des équipements.');
      })
      .finally(() => {
        if (!cancelled) setCatalogLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleItem(template: InternalLoadCatalogEntry) {
    const exists = study.equipment.find((e) => e.id === template.id);
    if (exists) {
      updateStudy(studyId, { equipment: study.equipment.filter((e) => e.id !== template.id) });
    } else {
      const item: EquipmentItem = {
        id: template.id,
        productId: template.productId,
        label: template.label,
        category: template.category,
        quantity: 1,
        unitPowerW: template.unitPowerW,
        usageHoursPerDay: template.usageHoursPerDay,
        simultaneityPercent: template.simultaneityPercent,
        selected: true,
      };
      updateStudy(studyId, { equipment: [...study.equipment, item] });
    }
  }

  const totalSimultaneousW = study.equipment.reduce((sum, e) => sum + simultaneousPowerW(e), 0);
  const totalInstalledW = study.equipment.reduce((sum, e) => sum + e.quantity * e.unitPowerW, 0);

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Quels équipements dégagent de la chaleur ?">
          <div className="flex flex-col divide-y divide-border">
            <div className="grid grid-cols-[1fr_auto_auto_auto] gap-2 pb-2 text-xs text-ink-faint">
              <span>Équipement</span>
              <span>Puissance</span>
              <span>Durée</span>
              <span>Sélection</span>
            </div>
            {catalogLoading && <p className="py-2.5 text-sm text-ink-faint">Chargement du catalogue…</p>}
            {catalogError && <p className="py-2.5 text-sm text-red-600">{catalogError}</p>}
            {!catalogLoading && !catalogError && catalog.length === 0 && (
              <p className="py-2.5 text-sm text-ink-faint">Aucun équipement disponible dans le catalogue.</p>
            )}
            {catalog.map((item) => {
              const selected = !!study.equipment.find((e) => e.id === item.id);
              return (
                <div key={item.id} className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-2 py-2.5 text-sm">
                  <span className="text-ink">{item.label}</span>
                  <span className="text-ink-soft">{item.unitPowerW} W</span>
                  <span className="text-ink-soft">{item.usageHoursPerDay} h/j</span>
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => toggleItem(item)}
                    className="h-4 w-4 accent-brand-600"
                    aria-label={`Sélectionner ${item.label}`}
                  />
                </div>
              );
            })}
          </div>
        </Card>

        <div className="flex flex-col gap-4">
          <Card title="Apports internes estimés">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-border p-4 text-center">
                <div className="text-xs text-ink-faint">Puissance installée</div>
                <div className="mt-1 text-lg font-semibold text-brand-700">{(totalInstalledW / 1000).toFixed(2)} kW</div>
              </div>
              <div className="rounded-xl border border-border p-4 text-center">
                <div className="text-xs text-ink-faint">Puissance simultanée</div>
                <div className="mt-1 text-lg font-semibold text-brand-700">{(totalSimultaneousW / 1000).toFixed(2)} kW</div>
              </div>
            </div>
          </Card>

          <Card title="Équipements ajoutés">
            {study.equipment.length === 0 ? (
              <p className="text-sm text-ink-faint">Aucun équipement sélectionné pour le moment.</p>
            ) : (
              <div className="flex flex-col divide-y divide-border">
                {study.equipment.map((e) => (
                  <div key={e.id} className="flex items-center justify-between py-2.5 text-sm">
                    <span className="flex items-center gap-2 text-ink">
                      <span className="text-brand-600">✓</span>
                      {e.label}
                    </span>
                    <span className="text-ink-soft">{simultaneousPowerW(e).toFixed(0)} W</span>
                  </div>
                ))}
                <div className="flex items-center justify-between pt-3 text-sm font-semibold text-ink">
                  <span>Total puissance simultanée</span>
                  <span>{(totalSimultaneousW / 1000).toFixed(2)} kW</span>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>

      <WizardFooter nextSteps={defaultNextSteps} onBack={goToPrevious} onContinue={goToNext} />
    </div>
  );
}
