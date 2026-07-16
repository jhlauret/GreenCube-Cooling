import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStudyStore } from '../store/studyStore';

export function NewStudyPage() {
  const createStudy = useStudyStore((state) => state.createStudy);
  const studyCount = useStudyStore((state) => Object.keys(state.studies).length);
  const navigate = useNavigate();
  const hasCreated = useRef(false);

  useEffect(() => {
    if (hasCreated.current) return;
    hasCreated.current = true;
    const id = createStudy(`Étude ${studyCount + 1}`);
    navigate(`/cooling/studies/${id}/location`, { replace: true });
  }, [createStudy, studyCount, navigate]);

  return null;
}
