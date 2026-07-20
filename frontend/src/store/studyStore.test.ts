import { beforeEach, describe, expect, it } from 'vitest';
import { useStudyStore, useSyncStatusStore } from './studyStore';

beforeEach(() => {
  useStudyStore.setState({ studies: {} });
  useSyncStatusStore.setState({ saving: {}, errors: {} });
});

describe('useStudyStore', () => {
  it('createStudy adds a draft with the given name and a fresh id', () => {
    const id = useStudyStore.getState().createStudy('Mon étude');
    const study = useStudyStore.getState().studies[id];
    expect(study).toBeDefined();
    expect(study.name).toBe('Mon étude');
    expect(study.backendId).toBeNull();
    expect(study.lastSyncedAt).toBeNull();
  });

  it('updateStudy bumps updatedAt', async () => {
    const id = useStudyStore.getState().createStudy('Étude');
    const before = useStudyStore.getState().studies[id].updatedAt;
    await new Promise((r) => setTimeout(r, 2));
    useStudyStore.getState().updateStudy(id, { name: 'Renommée' });
    const after = useStudyStore.getState().studies[id];
    expect(after.name).toBe('Renommée');
    expect(new Date(after.updatedAt).getTime()).toBeGreaterThan(new Date(before).getTime());
  });

  it('markSynced sets lastSyncedAt WITHOUT bumping updatedAt (no autosave feedback loop)', async () => {
    const id = useStudyStore.getState().createStudy('Étude');
    const updatedAtBefore = useStudyStore.getState().studies[id].updatedAt;
    await new Promise((r) => setTimeout(r, 2));

    useStudyStore.getState().markSynced(id, '2026-01-01T00:00:00.000Z');
    const study = useStudyStore.getState().studies[id];

    expect(study.lastSyncedAt).toBe('2026-01-01T00:00:00.000Z');
    expect(study.updatedAt).toBe(updatedAtBefore);
  });

  it('findByBackendId locates the draft tracking a given backend id', () => {
    const id = useStudyStore.getState().createStudy('Étude');
    useStudyStore.getState().updateStudy(id, { backendId: 42 });
    expect(useStudyStore.getState().findByBackendId(42)?.id).toBe(id);
    expect(useStudyStore.getState().findByBackendId(999)).toBeUndefined();
  });

  it('markStepComplete is idempotent', () => {
    const id = useStudyStore.getState().createStudy('Étude');
    useStudyStore.getState().markStepComplete(id, 'location');
    useStudyStore.getState().markStepComplete(id, 'location');
    expect(useStudyStore.getState().studies[id].completedSteps).toEqual(['location']);
  });

  it('updateStudy/markSynced/markStepComplete are no-ops for an unknown id', () => {
    expect(() => useStudyStore.getState().updateStudy('missing', { name: 'x' })).not.toThrow();
    expect(() => useStudyStore.getState().markSynced('missing', 'now')).not.toThrow();
    expect(() => useStudyStore.getState().markStepComplete('missing', 'location')).not.toThrow();
    expect(useStudyStore.getState().studies).toEqual({});
  });
});

describe('useSyncStatusStore', () => {
  it('tracks saving/error state independently per study id', () => {
    useSyncStatusStore.getState().setSaving('a', true);
    useSyncStatusStore.getState().setError('b', 'boom');

    expect(useSyncStatusStore.getState().saving.a).toBe(true);
    expect(useSyncStatusStore.getState().saving.b).toBeUndefined();
    expect(useSyncStatusStore.getState().errors.b).toBe('boom');
    expect(useSyncStatusStore.getState().errors.a).toBeUndefined();
  });
});
