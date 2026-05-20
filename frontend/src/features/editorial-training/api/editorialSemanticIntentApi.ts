export type EditorialSemanticIntentDto = {
  session_id: string;
  scene_index: number;
  clip_id: string;
  clip_source_taxonomy: string;
  auto_clip_source_taxonomy: string;
  human_clip_source_taxonomy: string | null;
  narrative_intent: string;
  auto_narrative_intent: string;
  human_narrative_intent: string | null;
  emotional_intent: string;
  auto_emotional_intent: string;
  human_emotional_intent: string | null;
  audio_fragment_text: string;
  visual_style_label: string;
  has_narrative_intent_override: boolean;
  has_clip_taxonomy_override: boolean;
};

export async function patchSceneSemanticIntent(
  sessionId: string,
  sceneIndex: number,
  patch: {
    human_narrative_intent?: string;
    human_clip_source_taxonomy?: string;
    human_emotional_intent?: string;
  },
): Promise<EditorialSemanticIntentDto> {
  const res = await fetch(`/editorial-semantic-intent/sessions/${sessionId}/scenes/${sceneIndex}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json() as Promise<EditorialSemanticIntentDto>;
}
