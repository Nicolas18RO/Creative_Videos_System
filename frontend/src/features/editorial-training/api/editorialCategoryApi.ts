export type EditorialCategoryOverrideDto = {
  session_id: string;
  scene_index: number;
  auto_narrative_role: string;
  human_narrative_role: string | null;
  effective_narrative_role: string;
  has_category_override: boolean;
};

export async function setSceneCategoryOverride(
  sessionId: string,
  sceneIndex: number,
  humanNarrativeRole: string,
  autoNarrativeRole?: string,
): Promise<EditorialCategoryOverrideDto> {
  const res = await fetch(`/editorial-category/sessions/${sessionId}/scenes/${sceneIndex}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      human_narrative_role: humanNarrativeRole,
      auto_narrative_role: autoNarrativeRole ?? null,
    }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `category_override_failed_${res.status}`);
  }
  return res.json() as Promise<EditorialCategoryOverrideDto>;
}
