import { useEffect, useRef } from 'react';
import type { StudyDraft } from '../types/study';
import { useStudyStore, useSyncStatusStore } from '../store/studyStore';
import { syncStudyToBackend } from './syncStudy';
import { ApiError } from '../api/client';

const DEBOUNCE_MS = 1500;

/**
 * Debounced background sync for the seven wizard step pages (Review and
 * Results already sync explicitly/synchronously before their own actions
 * and are left alone). Turns the local Zustand draft into a genuine
 * "controlled draft cache" instead of the sole source of truth: edits are
 * pushed to Odoo automatically a moment after the user stops typing,
 * without blocking the UI, and the result (saving/saved/error) is visible
 * via useSyncStatusStore + StudyDraft.lastSyncedAt (audit P0-04/GC-COOLING-06 pt.6).
 */
export function useAutosave(study: StudyDraft) {
  const markSynced = useStudyStore((state) => state.markSynced);
  const patchSilently = useStudyStore((state) => state.patchSilently);
  const setSaving = useSyncStatusStore((state) => state.setSaving);
  const setError = useSyncStatusStore((state) => state.setError);

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlightRef = useRef(false);
  const pendingRef = useRef(false);

  useEffect(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    timeoutRef.current = setTimeout(() => {
      void runSync();
    }, DEBOUNCE_MS);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
    // Only the content, not the identity of callbacks, should re-trigger
    // the debounce timer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [study.id, study.updatedAt]);

  async function runSync() {
    if (inFlightRef.current) {
      // A sync is already running for a slightly older version of the
      // draft — queue exactly one follow-up run instead of overlapping
      // requests that could race each other.
      pendingRef.current = true;
      return;
    }
    inFlightRef.current = true;
    setSaving(study.id, true);
    setError(study.id, null);
    try {
      const latest = useStudyStore.getState().studies[study.id];
      if (!latest) return;
      const backendId = await syncStudyToBackend(
        latest,
        (id) => patchSilently(latest.id, { backendId: id }),
        (equipment) => patchSilently(latest.id, { equipment }),
      );
      markSynced(latest.id, new Date().toISOString());
      void backendId;
    } catch (err) {
      setError(study.id, err instanceof ApiError ? err.message : 'La synchronisation automatique a échoué.');
    } finally {
      setSaving(study.id, false);
      inFlightRef.current = false;
      if (pendingRef.current) {
        pendingRef.current = false;
        void runSync();
      }
    }
  }
}
