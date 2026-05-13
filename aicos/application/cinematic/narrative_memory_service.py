"""Narrative Memory System (Fase 3): memoria de sesión, continuidad y bloqueo temático offline."""

from __future__ import annotations

import logging
import re

from sqlalchemy.orm import Session

from aicos.config import NarrativeMemoryConfig, get_config
from aicos.models.schemas import (
    ContinuityVisualBreakdown,
    GlobalContextSummary,
    NarrativeMemoryState,
    NarrativeSceneWindowEntry,
    Recommendation,
    Scene,
    SearchRankingContext,
    SearchRequest,
    SearchRunContext,
)
from aicos.services import narrative_memory_repository as nm_repo

logger = logging.getLogger(__name__)

_UNLOCK_NARRATIVE = frozenset({"CTA", "OUTRO", "RESULT", "BRAND"})

_COLOR_GROUPS: dict[str, frozenset[str]] = {
    "warm": frozenset({"warm", "cálido", "calido", "golden", "dorado", "orange", "naranja", "sepia"}),
    "cool": frozenset({"cool", "frío", "frio", "blue", "azul", "teal", "cyan"}),
    "neutral": frozenset({"neutral", "natural", "daylight", "gris", "grey", "gray"}),
    "high_key": frozenset({"bright", "high", "key", "luminoso", "blanco", "clean"}),
    "low_key": frozenset({"dark", "low", "key", "oscuro", "noir", "shadow"}),
    "neon": frozenset({"neon", "vibrant", "saturated", "saturado", "rgb"}),
}

_PACING_FAST = frozenset({"fast", "rápido", "rapido", "montage", "dynamic", "urgent"})
_PACING_SLOW = frozenset({"slow", "lento", "calm", "static", "still"})
_CAMERA = frozenset(
    {
        "handheld",
        "steadicam",
        "gimbal",
        "drone",
        "aerial",
        "static",
        "tripod",
        "dolly",
        "crane",
        "macro",
        "wide",
    }
)
_ENV_IN = frozenset(
    {"indoor", "interior", "studio", "office", "kitchen", "taller", "garage", "showroom", "cabin"}
)
_ENV_OUT = frozenset({"outdoor", "exterior", "street", "highway", "carretera", "landscape", "mountain", "beach"})

_FORBIDDEN_UNDER_AUTO_LOCK = (
    "recipe",
    "receta",
    "chef",
    "cocina",
    "kitchen",
    "food",
    "comida",
    "runway",
    "fashion",
    "vestido",
    "office",
    "corporate",
    "desk",
    "meeting",
    "reunión",
    "reunion",
    "coworking",
    "lifestyle vlog",
    "morning routine",
    "makeup tutorial",
)


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _tok(s: str) -> list[str]:
    raw = re.sub(r"[^\w\sáéíóúñü]", " ", s.lower(), flags=re.UNICODE)
    return [t for t in raw.split() if len(t) > 2]


def _clip_blob(r: Recommendation) -> str:
    parts = [
        r.clip_semantic_text or "",
        r.clip_subcategory or "",
        r.clip_context or "",
        r.clip_path or "",
        r.narrative_function or "",
    ]
    return " ".join(parts).lower()


def _color_family(blob: str) -> str:
    for fam, keys in _COLOR_GROUPS.items():
        if any(k in blob for k in keys):
            return fam
    return "unknown"


def _pacing_token(blob: str, nf: str | None) -> str:
    b = blob + " " + _norm(nf)
    if any(p in b for p in _PACING_FAST):
        return "fast"
    if any(p in b for p in _PACING_SLOW):
        return "slow"
    return "medium"


def _camera_token(blob: str) -> str:
    for c in sorted(_CAMERA, key=len, reverse=True):
        if c in blob:
            return c
    return "unknown"


def _environment_token(blob: str) -> str:
    if any(e in blob for e in _ENV_IN):
        return "indoor"
    if any(e in blob for e in _ENV_OUT):
        return "outdoor"
    return "mixed"


def _continuity_visual_scores(
    state: NarrativeMemoryState,
    blob: str,
    ranking: SearchRankingContext | None,
) -> ContinuityVisualBreakdown:
    """Heurísticos offline (sin visión por píxeles): proxies léxicos."""
    last = state.sliding_window[-1] if state.sliding_window else None
    cur_color = _color_family(blob)
    if last and last.color_token and cur_color != "unknown":
        color_sim = 1.0 if last.color_token == cur_color else 0.38
    else:
        color_sim = 0.55

    pt = _pacing_token(blob, ranking.narrative_function if ranking else None)
    if last and last.pacing_token:
        pacing = 1.0 if pt == last.pacing_token else 0.55 if {pt, last.pacing_token} == {"fast", "medium"} else 0.42
    else:
        pacing = 0.55

    ct = _camera_token(blob)
    if last and last.camera_token and last.camera_token != "unknown":
        camera = 1.0 if ct == last.camera_token else 0.5
    else:
        camera = 0.55

    env = _environment_token(blob)
    if last and last.environment_token:
        env_c = 1.0 if env == last.environment_token else 0.45
    else:
        env_c = 0.55

    prior_ent = set(state.recent_visual_entities)
    clip_toks = set(_tok(blob))
    if prior_ent and clip_toks:
        inter = len(prior_ent & clip_toks)
        union = len(prior_ent | clip_toks) or 1
        obj_p = 0.35 + 0.55 * (inter / union)
    else:
        obj_p = 0.52

    de = _norm(ranking.dominant_emotion if ranking else None) or _norm(state.dominant_emotion)
    mood_blob = blob + " " + _norm(ranking.scene_text if ranking else "")
    emo_c = 0.52
    if de in mood_blob or any(t in mood_blob for t in _tok(de)):
        emo_c = 0.82
    elif last and last.emotion_token and last.emotion_token in mood_blob:
        emo_c = 0.74

    return ContinuityVisualBreakdown(
        color_similarity=color_sim,
        pacing_compatibility=pacing,
        camera_movement_compatibility=camera,
        environment_consistency=env_c,
        object_persistence=obj_p,
        emotional_continuity=emo_c,
    )


def _composite_continuity(br: ContinuityVisualBreakdown) -> float:
    parts = (
        br.color_similarity,
        br.pacing_compatibility,
        br.camera_movement_compatibility,
        br.environment_consistency,
        br.object_persistence,
        br.emotional_continuity,
    )
    return max(0.0, min(1.0, sum(parts) / len(parts)))


def _arc_unlocked(scene_nf: str | None) -> bool:
    return (scene_nf or "").strip().upper() in _UNLOCK_NARRATIVE


def _industry_lock_violation(state: NarrativeMemoryState, blob: str, scene_nf: str | None) -> tuple[bool, str]:
    if not state.industry_lock_active or _arc_unlocked(scene_nf):
        return False, ""
    low = blob.lower()
    if any(b in low for b in _FORBIDDEN_UNDER_AUTO_LOCK):
        return True, "industry_lock_incompatible_blob"
    return False, ""


def _diversity_penalty(state: NarrativeMemoryState, r: Recommendation, cfg: NarrativeMemoryConfig) -> float:
    pen = 0.0
    if r.clip_id in state.previous_selected_clips:
        pen += cfg.max_repeat_clip_penalty
    sub = _norm(r.clip_subcategory)
    if not sub:
        return min(0.85, pen)
    same_sub = 0
    for w in state.sliding_window:
        frag = w.semantic_fragment.split("|", 1)[0]
        if _norm(frag) == sub:
            same_sub += 1
    if same_sub >= 2:
        pen += cfg.subcategory_loop_penalty * (same_sub - 1)
    return min(0.85, pen)


def _opening_automotive_cinematic(g: GlobalContextSummary | None) -> bool:
    if g is None:
        return False
    ind = _norm(g.industry)
    vs = _norm(g.visual_style)
    auto = "automotive" in ind or ind == "auto" or "motor" in ind
    cine = any(x in vs for x in ("cinematic", "dramatic", "commercial", "premium", "dark", "film"))
    return auto and cine


def initial_memory_state(correlation_id: str, g: GlobalContextSummary | None) -> NarrativeMemoryState:
    constraints: list[str] = []
    lock = False
    if _opening_automotive_cinematic(g):
        lock = True
        constraints.append("industry_lock_automotive_cinematic")
    if not g:
        return NarrativeMemoryState(
            session_correlation_id=correlation_id,
            narrative_session_db_id=correlation_id,
            continuity_constraints=constraints,
            industry_lock_active=lock,
        )
    ents = [str(x) for x in (g.semantic_entities or []) if str(x)]
    return NarrativeMemoryState(
        session_correlation_id=correlation_id,
        narrative_session_db_id=correlation_id,
        dominant_industry=g.industry or "general",
        dominant_emotion=g.dominant_emotion or "neutral",
        active_visual_style=g.visual_style or "unknown",
        narrative_flow=g.narrative_arc or "unknown",
        locked_opening_narrative_arc=g.narrative_arc,
        recent_visual_entities=ents[:24],
        continuity_constraints=constraints,
        industry_lock_active=lock,
    )


def load_state_for_scene(
    session: Session,
    correlation_id: str,
    scene_index: int,
    global_ctx: GlobalContextSummary | None,
    ranking: SearchRankingContext | None,
) -> NarrativeMemoryState:
    """Estado previo a la escena ``scene_index`` (instantánea scene_index-1 o inicial)."""
    if scene_index > 0:
        payload = nm_repo.load_snapshot_by_scene_index(session, correlation_id, scene_index - 1)
        if payload:
            st = NarrativeMemoryState.model_validate(payload)
            logger.info("[NarrativeMemory] state_loaded_from_snapshot scene=%s", scene_index)
            return st
    base = initial_memory_state(correlation_id, global_ctx)
    if ranking:
        merged_clips = list(dict.fromkeys(ranking.previous_selected_clip_ids or []))
        base.previous_selected_clips = merged_clips
    logger.info("[NarrativeFlow] state_initialized scene_index=%s lock=%s", scene_index, base.industry_lock_active)
    return base


def advance_state_after_selection(
    cfg: NarrativeMemoryConfig,
    prior: NarrativeMemoryState,
    *,
    scene_index: int,
    scene: Scene,
    top: Recommendation,
    global_ctx: GlobalContextSummary | None,
) -> NarrativeMemoryState:
    """Actualiza memoria deslizante y entidades tras elegir un clip."""
    blob = _clip_blob(top)
    entry = NarrativeSceneWindowEntry(
        scene_index=scene_index,
        clip_id=top.clip_id,
        concept_keywords=_tok(scene.concept or "")[:16],
        emotion_token=_norm(global_ctx.dominant_emotion if global_ctx else prior.dominant_emotion),
        visual_style_token=_norm(global_ctx.visual_style if global_ctx else prior.active_visual_style),
        pacing_token=_pacing_token(blob, scene.narrative_function),
        camera_token=_camera_token(blob),
        environment_token=_environment_token(blob),
        color_token=_color_family(blob),
        semantic_fragment=f"{_norm(top.clip_subcategory) or 'na'}|{blob[:180]}",
    )
    window = list(prior.sliding_window) + [entry]
    wsz = max(1, cfg.window_size)
    window = window[-wsz:]

    prev_clips = list(dict.fromkeys(prior.previous_selected_clips + [top.clip_id]))

    entities = list(dict.fromkeys(prior.recent_visual_entities + _tok(blob) + entry.concept_keywords))[:36]

    pacing_hint = entry.pacing_token
    pe = 0.55
    if pacing_hint == "fast":
        pe = 0.82
    elif pacing_hint == "slow":
        pe = 0.38
    energy = min(1.0, max(0.0, 0.85 * prior.cinematic_energy + 0.15 * pe))

    nfs = (prior.last_narrative_functions + [_norm(scene.narrative_function)])[-5:]
    lock_active = prior.industry_lock_active
    if _arc_unlocked(scene.narrative_function):
        lock_active = False
        logger.info("[NarrativeFlow] industry_lock_released_by_arc nf=%s", scene.narrative_function)

    constraints = list(prior.continuity_constraints)
    if not lock_active:
        constraints = [c for c in constraints if c != "industry_lock_automotive_cinematic"]
    elif lock_active and "industry_lock_automotive_cinematic" not in constraints:
        constraints.append("industry_lock_automotive_cinematic")

    return prior.model_copy(
        update={
            "sliding_window": window,
            "previous_selected_clips": prev_clips,
            "recent_visual_entities": entities,
            "cinematic_energy": energy,
            "last_narrative_functions": nfs,
            "industry_lock_active": lock_active,
            "dominant_industry": global_ctx.industry if global_ctx else prior.dominant_industry,
            "dominant_emotion": global_ctx.dominant_emotion if global_ctx else prior.dominant_emotion,
            "active_visual_style": global_ctx.visual_style if global_ctx else prior.active_visual_style,
            "narrative_flow": global_ctx.narrative_arc if global_ctx else prior.narrative_flow,
            "continuity_constraints": constraints,
        }
    )


class NarrativeMemoryService:
    """Evaluación de continuidad, bloqueo temático y diversidad controlada."""

    def __init__(self, cfg: NarrativeMemoryConfig) -> None:
        self.cfg = cfg

    def apply_for_search(
        self,
        session: Session,
        recs: list[Recommendation],
        req: SearchRequest,
        context: SearchRunContext,
    ) -> list[Recommendation]:
        if not self.cfg.enabled or not recs:
            return recs
        cid = context.correlation_id or ""
        if not cid or context.scene_index is None:
            return recs
        gctx = context.global_context
        ranking = context.ranking_context
        state = load_state_for_scene(session, cid, context.scene_index, gctx, ranking)
        scene_nf = ranking.narrative_function if ranking else req.narrative_function

        scored: list[tuple[Recommendation, float, ContinuityVisualBreakdown, float]] = []
        violation_logs = 0
        for r in recs:
            blob = _clip_blob(r)
            br = _continuity_visual_scores(state, blob, ranking)
            cont = _composite_continuity(br)
            viol, reason = _industry_lock_violation(state, blob, scene_nf)
            ind_mult = 1.0
            if viol:
                ind_mult = max(0.06, 1.0 - self.cfg.industry_lock_strength)
                logger.info(
                    "[ContinuityEngine] clip=%s violation=%s mult=%.3f",
                    r.clip_id,
                    reason,
                    ind_mult,
                )
                if violation_logs < 8:
                    nm_repo.log_continuity_decision(
                        session,
                        cid,
                        context.scene_index,
                        clip_id=r.clip_id,
                        decision_type="penalize",
                        reason_code=reason,
                        factors=br.model_dump(),
                    )
                    violation_logs += 1
            div_pen = _diversity_penalty(state, r, self.cfg)
            base = float(r.final_score)
            # Bonus acotado para evitar saturación y penalizaciones excesivas en cascada.
            raw_delta = (cont - 0.52) * 1.25
            cont_bonus = self.cfg.continuity_weight * max(-0.22, min(0.22, raw_delta))
            fs = base * (1.0 + cont_bonus) * ind_mult - self.cfg.diversity_weight * div_pen
            fs = max(0.0, min(1.0, fs))
            logger.info(
                "[VisualConsistency] clip=%s cont=%.3f div_pen=%.3f final=%.4f color=%.2f pace=%.2f",
                r.clip_id,
                cont,
                div_pen,
                fs,
                br.color_similarity,
                br.pacing_compatibility,
            )
            scored.append((r, fs, br, cont))

        scored.sort(key=lambda x: (-x[1], x[0].clip_id))
        out = [
            t[0].model_copy(update={"final_score": t[1], "similarity_score": float(t[0].similarity_score)})
            for t in scored
        ]
        if scored:
            top_t = scored[0]
            viol_top, _ = _industry_lock_violation(state, _clip_blob(top_t[0]), scene_nf)
            ind_cons = 0.0 if viol_top else 1.0
            logger.info(
                "[NarrativeMemory] scene_index=%s continuity_score=%.3f industry_consistency=%.2f "
                "top_clip=%s memory_final=%.4f pool=%d",
                context.scene_index,
                top_t[3],
                ind_cons,
                top_t[0].clip_id,
                top_t[1],
                len(scored),
            )
        else:
            logger.info("[NarrativeMemory] scene_index=%s empty_pool_skip=true", context.scene_index)
        return out

    def persist_after_top_selection(
        self,
        session: Session,
        *,
        correlation_id: str,
        scene_index: int,
        top: Recommendation,
        scene: Scene,
        global_ctx: GlobalContextSummary | None,
        ranking: SearchRankingContext | None,
    ) -> None:
        """Persiste estado y decisiones tras cerrar la escena (clip rank 1)."""
        if not self.cfg.enabled or not correlation_id:
            return
        prior = load_state_for_scene(session, correlation_id, scene_index, global_ctx, ranking)
        new_state = advance_state_after_selection(self.cfg, prior, scene_index=scene_index, scene=scene, top=top, global_ctx=global_ctx)
        nm_repo.save_state_snapshot(session, correlation_id, scene_index, new_state.model_dump())
        blob = _clip_blob(top)
        br = _continuity_visual_scores(prior, blob, ranking)
        cont = _composite_continuity(br)
        nm_repo.log_clip_selection(
            session,
            correlation_id,
            scene_index,
            clip_id=top.clip_id,
            rank_chosen=1,
            final_score=float(top.final_score),
            continuity_blend=cont,
            extra={"continuity": br.model_dump()},
        )
        session.flush()
        logger.info("[NarrativeMemory] persist_done session=%s scene=%s", correlation_id, scene_index)


def get_narrative_memory_service() -> NarrativeMemoryService:
    try:
        cfg = get_config().narrative_memory
    except Exception as e:
        logger.warning("[NarrativeMemory] get_config_fallback defaults: %s", e)
        cfg = NarrativeMemoryConfig()
    return NarrativeMemoryService(cfg)
