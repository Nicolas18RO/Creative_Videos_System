/** Persistencia de sesión del studio en localStorage (restauración tras refresh). */

const KEY = "aicos.studio.session.v1";

export type StudioSessionPersisted = {
  projectId: string | null;
  sceneId: string | null;
};

export function loadStudioSession(): StudioSessionPersisted | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StudioSessionPersisted;
    if (typeof parsed !== "object" || parsed === null) return null;
    return {
      projectId: parsed.projectId ?? null,
      sceneId: parsed.sceneId ?? null,
    };
  } catch {
    return null;
  }
}

export function saveStudioSession(session: StudioSessionPersisted): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(session));
  } catch {
    /* quota / private mode */
  }
}

export function clearStudioSession(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
