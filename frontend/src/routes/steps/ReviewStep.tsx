import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useWizardNav } from '../useWizardNav';
import type { StudyDraft } from '../../types/study';

export function ReviewStep() {
  const { study } = useOutletContext<{ study: StudyDraft }>();
  const { goToPrevious, goToNext } = useWizardNav('review');

  const glazedArea = study.orientation.facades.filter((f) => f.enabled).reduce((s, f) => s + f.glazedAreaM2, 0);

  const attentionPoints: { message: string; severity: 'low' | 'medium' }[] = [];
  if (study.orientation.solarProtections.length === 0 && glazedArea > 0) {
    attentionPoints.push({ message: 'Aucune protection solaire spécifiée.', severity: 'medium' });
  }
  if (study.model.airtightnessN50 === 0) {
    attentionPoints.push({ message: "Étanchéité à l'air non renseignée.", severity: 'low' });
  }
  if (study.equipment.length === 0) {
    attentionPoints.push({ message: 'Aucun équipement thermique renseigné.', severity: 'low' });
  }
  if (!study.location.climateConfirmed) {
    attentionPoints.push({ message: 'Contexte climatique non confirmé.', severity: 'medium' });
  }

  const totalFields = 24;
  const completedFields =
    totalFields -
    (study.location.climateConfirmed ? 0 : 3) -
    (study.orientation.solarProtections.length === 0 ? 2 : 0) -
    (study.equipment.length === 0 ? 3 : 0);
  const reliabilityPercent = Math.round((completedFields / totalFields) * 100);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h1 className="text-xl font-semibold text-ink">Vérifiez les données avant le calcul BTU</h1>
            <p className="mt-1 text-sm text-ink-soft">
              Passez en revue les paramètres saisis. Les éléments estimés ou manquants peuvent impacter la précision du calcul.
            </p>
          </div>
          <div className="w-full sm:w-64">
            <div className="flex items-baseline justify-between text-sm">
              <span className="text-ink-faint">Fiabilité des données</span>
              <span className="text-lg font-semibold text-brand-700">{reliabilityPercent} %</span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-surface-muted">
              <div className="h-full bg-brand-600" style={{ width: `${reliabilityPercent}%` }} />
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <ReviewCard title="Site" confirmed={study.location.climateConfirmed}>
          <ReviewRow label="Adresse" value={study.location.address || '—'} />
          <ReviewRow
            label="Coordonnées"
            value={study.location.latitude ? `${study.location.latitude.toFixed(4)}, ${study.location.longitude?.toFixed(4)}` : '—'}
          />
          <ReviewRow label="Altitude" value={study.location.altitudeM ? `${study.location.altitudeM} m` : '—'} />
        </ReviewCard>

        <ReviewCard title="GreenCube" confirmed>
          <ReviewRow label="Modèle" value={study.model.modelCode} />
          <ReviewRow
            label="Dimensions"
            value={`${study.model.lengthM} x ${study.model.widthM} x ${study.model.heightM} m`}
          />
          <ReviewRow label="U moyen" value={`${study.model.uValueWm2k} W/m².K`} />
        </ReviewCard>

        <ReviewCard title="Orientation & vitrages" confirmed={glazedArea > 0}>
          <ReviewRow label="Orientation" value={study.orientation.mainOrientation} />
          <ReviewRow label="Surface vitrée" value={`${glazedArea.toFixed(1)} m²`} />
          <ReviewRow label="Protections" value={study.orientation.solarProtections.length ? study.orientation.solarProtections.join(', ') : 'Aucune'} />
        </ReviewCard>

        <ReviewCard title="Usage" confirmed>
          <ReviewRow label="Type" value={study.usage.usageType} />
          <ReviewRow label="Occupation" value={`${study.usage.usualOccupants} personnes`} />
          <ReviewRow label="Horaires" value={`${study.usage.occupancyStartHour}h - ${study.usage.occupancyEndHour}h`} />
        </ReviewCard>

        <ReviewCard title="Équipements" estimated>
          <ReviewRow label="Nombre" value={`${study.equipment.length} équipements`} />
          <ReviewRow
            label="Puissance simultanée"
            value={`${(study.equipment.reduce((s, e) => s + e.quantity * e.unitPowerW * (e.simultaneityPercent / 100), 0) / 1000).toFixed(2)} kW`}
          />
        </ReviewCard>

        <ReviewCard title="Ventilation" estimated>
          <ReviewRow label="Type" value={study.comfort.ventilationSystem} />
          <ReviewRow label="Débit" value={`${study.comfort.estimatedAirflowM3h} m³/h`} />
        </ReviewCard>

        <ReviewCard title="Confort" estimated>
          <ReviewRow label="Température" value={`${study.comfort.targetTemperatureRange} °C`} />
          <ReviewRow label="Humidité" value={`${study.comfort.targetHumidityRange} %`} />
          <ReviewRow label="Niveau de service" value={study.comfort.serviceLevel} />
        </ReviewCard>

        <Card title="Points d'attention" className="sm:col-span-2 lg:col-span-1">
          {attentionPoints.length === 0 ? (
            <p className="text-sm text-ink-soft">Aucun point d'attention détecté.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {attentionPoints.map((p) => (
                <div key={p.message} className="flex items-center justify-between gap-2 text-sm">
                  <span className="text-ink-soft">⚠ {p.message}</span>
                  <Badge tone={p.severity === 'medium' ? 'warn' : 'neutral'}>
                    {p.severity === 'medium' ? 'Moyen' : 'Faible'}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-medium text-ink">✅ Synthèse prête pour le solver</p>
          <p className="mt-1 text-sm text-ink-soft">
            Le solver utilisera ces données pour estimer la puissance de refroidissement (BTU/h) et proposer le
            dimensionnement recommandé.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={goToPrevious}>
            ← Retour
          </Button>
          <Button onClick={goToNext}>Calculer la puissance de refroidissement →</Button>
        </div>
      </Card>
    </div>
  );
}

function ReviewCard({
  title,
  confirmed,
  estimated,
  children,
}: {
  title: string;
  confirmed?: boolean;
  estimated?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card
      title={title}
      action={
        confirmed ? <Badge tone="brand">Confirmé</Badge> : estimated ? <Badge tone="warn">Estimé</Badge> : undefined
      }
    >
      <div className="flex flex-col gap-1.5 text-sm">{children}</div>
    </Card>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-ink-faint">{label}</span>
      <span className="text-right font-medium text-ink">{value}</span>
    </div>
  );
}
