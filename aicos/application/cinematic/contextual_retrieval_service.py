"""Contextual Retrieval Engine: señales multicapa y reranking sin tocar Chroma."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aicos.application.cinematic.continuity_analyzer_service import ContinuityAnalyzerService
from aicos.config import ContextualRetrievalConfig
from aicos.models.schemas import Recommendation, SearchRankingContext, SearchRequest

if TYPE_CHECKING:
    from aicos.core.embedder import Embedder

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RetrievalSignals:
    """Señales 0..1 (o penalizaciones) por candidato."""

    semantic_score: float
    global_context_score: float
    narrative_score: float
    domain_score: float
    emotion_score: float
    continuity_score: float
    cinematic_style_score: float
    industry_match: float
    object_match: float
    emotion_match: float
    narrative_match: float
    cinematic_style_match: float
    visual_intent_match: float
    semantic_anchor_overlap: float
    domain_mismatch_penalty: float


@dataclass(frozen=True, slots=True)
class RankingContext:
    """Vista mínima para ranking (alias lógico de ``SearchRankingContext`` en capa aplicación)."""

    industry: str | None
    topic: str | None
    dominant_emotion: str | None
    semantic_anchors: tuple[str, ...]
    narrative_arc: str | None
    visual_style: str | None
    content_intent: str | None
    scene_text: str | None
    scene_concept: str | None
    narrative_function: str | None

    @staticmethod
    def from_schema(ctx: SearchRankingContext) -> RankingContext:
        return RankingContext(
            industry=ctx.industry,
            topic=ctx.topic,
            dominant_emotion=ctx.dominant_emotion,
            semantic_anchors=tuple(ctx.semantic_anchors or ()),
            narrative_arc=ctx.narrative_arc,
            visual_style=ctx.visual_style,
            content_intent=ctx.content_intent,
            scene_text=ctx.scene_text,
            scene_concept=ctx.scene_concept,
            narrative_function=ctx.narrative_function,
        )


def _norm_industry(s: str | None) -> str:
    return (s or "").strip().lower()


def _clip_blob(rec: Recommendation) -> str:
    parts = [
        rec.clip_semantic_text or "",
        rec.clip_subcategory or "",
        rec.clip_context or "",
        rec.clip_path or "",
        rec.narrative_function or "",
    ]
    return " ".join(parts).lower()


def _jaccard_tokens(a: str, b: str) -> float:
    ta = {x for x in a.lower().split() if len(x) > 2}
    tb = {x for x in b.lower().split() if len(x) > 2}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


class ContextualRetrievalService:
    """Reranking híbrido post-recuperación vectorial (Chroma intacto)."""

    def __init__(self, cfg: ContextualRetrievalConfig) -> None:
        self.cfg = cfg
        self._continuity = ContinuityAnalyzerService()

    def apply_pipeline(
        self,
        recs: list[Recommendation],
        req: SearchRequest,
        ranking: SearchRankingContext,
        embedder: Embedder | None = None,
    ) -> list[Recommendation]:
        if not self.cfg.enabled or not recs:
            return recs
        t0 = time.perf_counter()
        rc = RankingContext.from_schema(ranking)
        pool = recs if not self.cfg.lazy_rerank else recs[: max(self.cfg.top_k_rerank, req.candidate_pool_size * 2)]
        scored: list[tuple[Recommendation, float, RetrievalSignals]] = []
        global_vec: list[float] | None = None
        clip_vecs: dict[str, list[float]] = {}
        if self.cfg.use_batch_context_embedding and embedder is not None:
            global_vec, clip_vecs = self._batch_global_vs_clips(pool, ranking, embedder)

        for r in pool:
            sig = self._compute_signals(r, rc, ranking, global_vec, clip_vecs.get(r.clip_id) if clip_vecs else None)
            hybrid = self._hybrid_score(sig)
            hybrid *= self._domain_filter_multiplier(rc, r)
            scored.append((r, hybrid, sig))

        scored.sort(key=lambda x: (-x[1], x[0].clip_id))
        logger.info("[NarrativeRerank] top_after_domain=%s", scored[0][0].clip_id if scored else "none")
        scored = self._diversity_balance(scored)

        out: list[Recommendation] = []
        for r, hybrid, sig in scored:
            new_final = max(0.0, min(1.0, hybrid + float(r.taxonomy_boost)))
            logger.info(
                "[RankingSignals] clip=%s hybrid=%.4f industry_match=%.2f anchor_ovl=%.2f domain_pen=%.2f",
                r.clip_id,
                hybrid,
                sig.industry_match,
                sig.semantic_anchor_overlap,
                sig.domain_mismatch_penalty,
            )
            out.append(
                r.model_copy(
                    update={
                        "final_score": new_final,
                        "similarity_score": float(r.similarity_score),
                    }
                )
            )
        out.sort(key=lambda x: (-x.final_score, x.clip_id))
        tail = recs[len(pool) :] if len(pool) < len(recs) else []
        merged = out + tail
        logger.info(
            "[ContextualRetrieval] reranked=%d pool=%d elapsed_ms=%.1f",
            len(out),
            len(pool),
            (time.perf_counter() - t0) * 1000,
        )
        return merged

    def _hybrid_score(self, s: RetrievalSignals) -> float:
        c = self.cfg
        w = {
            "semantic": c.weight_semantic,
            "global": c.weight_global_context,
            "narrative": c.weight_narrative,
            "domain": c.weight_domain,
            "emotion": c.weight_emotion,
            "continuity": c.weight_continuity,
            "cinematic": c.weight_cinematic_style,
        }
        total = sum(w.values()) or 1.0
        return (
            w["semantic"] / total * s.semantic_score
            + w["global"] / total * s.global_context_score
            + w["narrative"] / total * s.narrative_score
            + w["domain"] / total * s.domain_score
            + w["emotion"] / total * s.emotion_score
            + w["continuity"] / total * s.continuity_score
            + w["cinematic"] / total * s.cinematic_style_score
        )

    def _batch_global_vs_clips(
        self,
        pool: list[Recommendation],
        ranking: SearchRankingContext,
        embedder: Embedder,
    ) -> tuple[list[float] | None, dict[str, list[float]]]:
        """Embeddings en lote (opcional): texto global vs fragmentos de clip."""
        try:
            gline = " ".join(
                filter(
                    None,
                    [
                        ranking.topic or "",
                        ranking.industry or "",
                        " ".join(ranking.semantic_anchors or []),
                    ],
                )
            ).strip()[:2000]
            if not gline:
                return None, {}
            texts = [gline]
            ids: list[str] = []
            for r in pool:
                st = (r.clip_semantic_text or "")[:1200]
                if st:
                    texts.append(st)
                    ids.append(r.clip_id)
            if len(texts) < 2:
                return None, {}
            bs = self.cfg.embedding_batch_size or 16
            vecs = embedder.embed_batch(texts, batch_size=bs)
            gv = vecs[0]
            out: dict[str, list[float]] = {}
            for i, cid in enumerate(ids, start=1):
                out[cid] = vecs[i]
            return gv, out
        except Exception as e:
            logger.warning("[ContextualRetrieval] batch_embed_skip error=%s", e)
            return None, {}

    def _embedding_cosine(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na < 1e-9 or nb < 1e-9:
            return 0.0
        return max(0.0, min(1.0, dot / (na * nb)))

    def _compute_signals(
        self,
        r: Recommendation,
        rc: RankingContext,
        ranking: SearchRankingContext,
        global_vec: list[float] | None,
        clip_vec: list[float] | None,
    ) -> RetrievalSignals:
        sem = max(0.0, min(1.0, float(r.similarity_score)))
        blob = _clip_blob(r)
        anchor_blob = " ".join(rc.semantic_anchors) + " " + (rc.topic or "")
        anchor_ovl = _jaccard_tokens(anchor_blob, blob)
        if anchor_ovl < len(rc.semantic_anchors) * 0.08 and any(a in blob for a in rc.semantic_anchors if len(a) > 2):
            anchor_ovl = max(anchor_ovl, 0.35)
        g_lex = max(0.0, min(1.0, 0.55 * anchor_ovl + 0.45 * _contains_industry(blob, rc.industry)))
        g_emb = 0.0
        if global_vec is not None and clip_vec is not None:
            g_emb = self._embedding_cosine(global_vec, clip_vec)
        global_score = max(0.0, min(1.0, (1.0 - self.cfg.embedding_blend) * g_lex + self.cfg.embedding_blend * g_emb))
        ci_raw = (rc.content_intent or "").strip().lower()
        ci = ci_raw if ci_raw and ci_raw != "unknown" else ""
        vim_pre = min(1.0, anchor_ovl + 0.15 * (1.0 if ci and ci in blob else 0.0))
        global_score = max(0.0, min(1.0, 0.88 * global_score + 0.12 * vim_pre))

        sn = (rc.narrative_function or "").upper()
        cn = (r.narrative_function or "").upper()
        narrative = 0.45
        if sn and cn:
            if sn == cn:
                narrative = 1.0
            elif sn[:4] == cn[:4]:
                narrative = 0.72
        arc = (rc.narrative_arc or "").lower()
        if "problem" in arc and "PROBLEM" in cn:
            narrative = max(narrative, 0.88)
        if "solution" in arc and cn in ("BENEFIT", "RESULT", "CTA"):
            narrative = max(narrative, 0.85)

        dom, ind_m, pen = self._domain_scores(rc, blob)

        emo = self._emotion_score(rc, blob, ranking.scene_text or "")

        cont = self._continuity.score(r, ranking)

        cin = self._cinematic_score(rc, blob)

        vim = vim_pre

        return RetrievalSignals(
            semantic_score=sem,
            global_context_score=global_score,
            narrative_score=narrative,
            domain_score=dom,
            emotion_score=emo,
            continuity_score=cont,
            cinematic_style_score=cin,
            industry_match=ind_m,
            object_match=anchor_ovl,
            emotion_match=emo,
            narrative_match=narrative,
            cinematic_style_match=cin,
            visual_intent_match=vim,
            semantic_anchor_overlap=anchor_ovl,
            domain_mismatch_penalty=pen,
        )

    def _domain_scores(self, rc: RankingContext, blob: str) -> tuple[float, float, float]:
        ind = _norm_industry(rc.industry)
        pen = 0.0
        if not ind or ind == "general":
            return 0.58, 0.5, pen
        hit = _contains_industry(blob, rc.industry)
        ind_m = 1.0 if hit else 0.35
        base = 0.55 + 0.45 * (1.0 if hit else 0.0)
        if ind == "automotive":
            bad, good = _automotive_mismatch(blob)
            if bad and not good:
                pen = 0.72
                base *= 0.28
                ind_m = min(ind_m, 0.25)
            elif bad and good:
                pen = 0.25
                base *= 0.72
        return max(0.0, min(1.0, base)), ind_m, pen

    def _domain_filter_multiplier(self, rc: RankingContext, rec: Recommendation) -> float:
        _, _, pen = self._domain_scores(rc, _clip_blob(rec))
        return max(0.15, 1.0 - pen)

    def _emotion_score(self, rc: RankingContext, blob: str, scene_text: str) -> float:
        de = (rc.dominant_emotion or "").lower()
        mood_blob = (scene_text + " " + blob).lower()
        if de == "concern" and any(x in mood_blob for x in ("damage", "daño", "worry", "peligro", "risk")):
            return 0.88
        if de == "trust" and any(x in mood_blob for x in ("guarantee", "garant", "certified")):
            return 0.82
        if de == "excitement" and any(x in mood_blob for x in ("wow", "amazing", "increíble")):
            return 0.8
        return 0.52

    def _cinematic_score(self, rc: RankingContext, blob: str) -> float:
        vs = (rc.visual_style or "").lower()
        if not vs or vs == "unknown":
            return 0.5
        keys = vs.replace("_", " ").split()
        hits = sum(1 for k in keys if len(k) > 2 and k in blob)
        return max(0.35, min(0.95, 0.4 + 0.12 * hits))

    def _diversity_balance(
        self,
        scored: list[tuple[Recommendation, float, RetrievalSignals]],
    ) -> list[tuple[Recommendation, float, RetrievalSignals]]:
        if not self.cfg.diversity_balance_enabled or len(scored) < 4:
            return scored
        seen: dict[str, int] = {}
        adj: list[tuple[Recommendation, float, RetrievalSignals]] = []
        for r, h, s in scored:
            sub = (r.clip_subcategory or "na").lower()[:48]
            c = seen.get(sub, 0)
            dh = h - c * self.cfg.diversity_subcategory_penalty
            seen[sub] = c + 1
            adj.append((r, dh, s))
        adj.sort(key=lambda x: (-x[1], x[0].clip_id))
        logger.info("[ContextualRetrieval] diversity_pass adjusted=%d", len(adj))
        return adj


def _contains_industry(blob: str, industry: str | None) -> float:
    ind = _norm_industry(industry)
    if not ind:
        return 0.0
    synonyms: dict[str, tuple[str, ...]] = {
        "automotive": ("auto", "car", "motor", "engine", "vehic", "oil", "aceite", "taller", "mechan"),
        "cosmetics": ("skin", "piel", "cream", "crema", "beauty", "makeup", "maquill"),
        "medical": ("health", "salud", "doctor", "clinic", "patient", "paciente"),
    }
    for key, words in synonyms.items():
        if key in ind or ind in key:
            if any(w in blob for w in words):
                return 1.0
    return 1.0 if ind in blob else 0.0


def _automotive_mismatch(blob: str) -> tuple[bool, bool]:
    """Retorna (señales negativas, señales positivas automotrices)."""
    bad_food = ("recipe", "receta", "kitchen", "cocina", "chef", "food", "comida", "bake", "pastel")
    bad_fashion = ("runway", "fashion week", "outfit", "dress", "vestido", "makeup tutorial")
    bad_smoke = ("wildfire", "forest fire", "incendio forestal", "bomberos", "firefighter rescue")
    good = ("motor", "engine", "oil", "aceite", "exhaust", "escape", "cylinder", "piston", "automotive", "car", "coche", "taller", "mechan")
    bad = any(b in blob for b in bad_food + bad_fashion + bad_smoke)
    g = any(b in blob for b in good)
    if "humo" in blob or "smoke" in blob:
        if any(x in blob for x in ("incendio", "fire", "quem", "burn")) and not g:
            bad = True
    return bad, g


def get_contextual_retrieval_service() -> ContextualRetrievalService:
    from aicos.config import get_config

    return ContextualRetrievalService(get_config().contextual_retrieval)
