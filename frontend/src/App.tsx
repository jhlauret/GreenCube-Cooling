import { Navigate, Route, Routes } from 'react-router-dom';
import { StudiesListPage } from './routes/StudiesListPage';
import { NewStudyPage } from './routes/NewStudyPage';
import { StudyLayout } from './routes/StudyLayout';
import { LocationStep } from './routes/steps/LocationStep';
import { ModelStep } from './routes/steps/ModelStep';
import { OrientationStep } from './routes/steps/OrientationStep';
import { UsageStep } from './routes/steps/UsageStep';
import { EquipmentStep } from './routes/steps/EquipmentStep';
import { ComfortStep } from './routes/steps/ComfortStep';
import { ReviewStep } from './routes/steps/ReviewStep';
import { ResultsPage } from './routes/ResultsPage';
import { EquipmentSelectionPage } from './routes/EquipmentSelectionPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/cooling/studies" replace />} />
      <Route path="/cooling/studies" element={<StudiesListPage />} />
      <Route path="/cooling/studies/new" element={<NewStudyPage />} />
      <Route path="/cooling/studies/:studyId" element={<StudyLayout />}>
        <Route index element={<Navigate to="location" replace />} />
        <Route path="location" element={<LocationStep />} />
        <Route path="model" element={<ModelStep />} />
        <Route path="orientation" element={<OrientationStep />} />
        <Route path="usage" element={<UsageStep />} />
        <Route path="equipment" element={<EquipmentStep />} />
        <Route path="comfort" element={<ComfortStep />} />
        <Route path="review" element={<ReviewStep />} />
      </Route>
      <Route path="/cooling/studies/:studyId/results" element={<ResultsPage />} />
      <Route path="/cooling/studies/:studyId/equipment-selection" element={<EquipmentSelectionPage />} />
      <Route path="*" element={<Navigate to="/cooling/studies" replace />} />
    </Routes>
  );
}
