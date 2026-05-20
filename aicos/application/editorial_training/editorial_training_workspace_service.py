"""Orquesta sesiones de entrenamiento, persistencia de timeline y refuerzo 6.6 (Fase 6.7)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from aicos.application.editorial_dataset.creative_timeline_builder_service import CreativeTimelineBuilderService
from aicos.application.editorial_dataset.ports import CreativeTimelinePersistenceReadPort, RawTimelineSceneInput
from aicos.application.editorial_training.ports import (
    EditorialStyleEmbeddingAttachPort,
    EditorialTrainingSessionPersistencePort,
)
from aicos.application.human_feedback.human_feedback_reinforcement_service import (
    HumanFeedbackReinforcementService,
    IngestEditorialHumanFeedbackCommand,
)
from aicos.config import AppConfig, EditorialTrainingWorkspaceConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline
from aicos.domain.editorial_training.entities import (
    EditorialTrainingCorrectionItem,
    EditorialTrainingSession,
    EditorialTrainingSessionStatus,
)
from aicos.domain.editorial_training.rules import validate_correction_reward

logger = logging.getLogger(__name__)


class EditorialTrainingWorkspaceService:
    def __init__(
        self,
        *,
        workspace_cfg: EditorialTrainingWorkspaceConfig,
        app_cfg: AppConfig,
        persistence: EditorialTrainingSessionPersistencePort,
        timeline_builder: CreativeTimelineBuilderService,
        timeline_read: CreativeTimelinePersistenceReadPort,
        human_feedback: HumanFeedbackReinforcementService | None,
        style_embedding_attach: EditorialStyleEmbeddingAttachPort,
    ) -> None:
        self._workspace_cfg = workspace_cfg
        self._app_cfg = app_cfg
        self._persistence = persistence
        self._timeline_builder = timeline_builder
        self._timeline_read = timeline_read
        self._human_feedback = human_feedback
        self._style_embedding_attach = style_embedding_attach

    def _require_enabled(self) -> None:
        if not self._workspace_cfg.enabled:
            raise ValueError("editorial_training_workspace_disabled")

    def _get_or_raise(self, session: Any, session_id: str) -> EditorialTrainingSession:
        s = self._persistence.get_by_id(session, session_id)
        if s is None:
            raise ValueError("editorial_training_session_not_found")
        return s

    def create_session(
        self,
        session: Any,
        *,
        creative_id: str,
        project_id: str | None,
        final_video_path: str = "",
        audio_path: str = "",
        project_label: str = "",
        creative_label: str = "",
        product_category: str = "",
        notes: str = "",
    ) -> EditorialTrainingSession:
        self._require_enabled()
        cid = (creative_id or "").strip()
        if not cid:
            raise ValueError("creative_id_required")
        now = datetime.now(timezone.utc)
        sid = str(uuid.uuid4())
        fv = (final_video_path or "").strip()
        ap = (audio_path or "").strip()
        status = (
            EditorialTrainingSessionStatus.READY
            if (fv and ap)
            else EditorialTrainingSessionStatus.DRAFT
        )
        s = EditorialTrainingSession(
            session_id=sid,
            creative_id=cid,
            project_id=(project_id or "").strip() or None,
            status=status,
            final_video_path=fv,
            audio_path=ap,
            corrections=(),
            created_at=now,
            updated_at=now,
            project_label=(project_label or "").strip()[:512],
            creative_label=(creative_label or "").strip()[:512],
            product_category=(product_category or "").strip()[:256],
            notes=(notes or "").strip()[:4000],
        )
        self._persistence.save(session, s)
        logger.info("[EditorialTraining] session_created id=%s creative=%s", sid, cid)
        return s

    def persist_training_session(self, session: Any, training: EditorialTrainingSession) -> None:
        self._require_enabled()
        self._persistence.save(session, training)

    def update_session_status(self, session: Any, session_id: str, status: str) -> EditorialTrainingSession:
        self._require_enabled()
        s = self._get_or_raise(session, session_id)
        now = datetime.now(timezone.utc)
        out = replace(s, status=status, updated_at=now)
        self._persistence.save(session, out)
        return out

    def update_media_paths(
        self,
        session: Any,
        session_id: str,
        *,
        final_video_path: str | None = None,
        audio_path: str | None = None,
    ) -> EditorialTrainingSession:
        self._require_enabled()
        s = self._get_or_raise(session, session_id)
        if s.status == EditorialTrainingSessionStatus.ANALYZING:
            raise ValueError("editorial_training_uploads_blocked_during_analyze")
        if s.status == EditorialTrainingSessionStatus.COMMITTED:
            raise ValueError("editorial_training_uploads_blocked_after_commit")
        fv = s.final_video_path if final_video_path is None else (final_video_path or "").strip()
        ap = s.audio_path if audio_path is None else (audio_path or "").strip()
        now = datetime.now(timezone.utc)
        video_changed = final_video_path is not None and fv != s.final_video_path
        audio_changed = audio_path is not None and ap != s.audio_path
        if s.status == EditorialTrainingSessionStatus.FAILED:
            st = EditorialTrainingSessionStatus.DRAFT
        elif s.status == EditorialTrainingSessionStatus.AWAITING_HUMAN and (video_changed or audio_changed):
            st = EditorialTrainingSessionStatus.DRAFT
        else:
            st = s.status
        if fv and ap and st == EditorialTrainingSessionStatus.DRAFT:
            st = EditorialTrainingSessionStatus.READY
        elif not (fv and ap):
            st = EditorialTrainingSessionStatus.DRAFT
        out = replace(s, final_video_path=fv, audio_path=ap, status=st, updated_at=now)
        self._persistence.save(session, out)
        logger.info("[EditorialTraining] media_paths_updated session=%s", session_id)
        return out

    def get_session(self, session: Any, session_id: str) -> EditorialTrainingSession | None:
        self._require_enabled()
        return self._persistence.get_by_id(session, session_id)

    def load_timeline(self, session: Any, creative_id: str) -> CreativeTimeline | None:
        self._require_enabled()
        return self._timeline_read.get_by_creative_id(session, creative_id)

    def submit_timeline(
        self,
        session: Any,
        session_id: str,
        raw_scenes: tuple[RawTimelineSceneInput, ...],
        *,
        from_auto_detection: bool = False,
    ) -> CreativeTimeline:
        self._require_enabled()
        s = self._get_or_raise(session, session_id)
        if s.status not in (
            EditorialTrainingSessionStatus.DRAFT,
            EditorialTrainingSessionStatus.READY,
            EditorialTrainingSessionStatus.ANALYZING,
            EditorialTrainingSessionStatus.AWAITING_HUMAN,
        ):
            raise ValueError("editorial_training_invalid_status_for_timeline_submit")
        from aicos.services.editorial_semantic_intent_factory import build_editorial_semantic_intent_service

        semantic_svc = build_editorial_semantic_intent_service()
        merged_raw = semantic_svc.prepare_raw_for_timeline_build(
            session,
            session_id,
            raw_scenes,
            from_auto_detection=from_auto_detection,
        )
        timeline = self._timeline_builder.build_from_raw_scenes(
            creative_id=s.creative_id,
            audio_path=s.audio_path,
            final_video_path=s.final_video_path,
            raw_scenes=merged_raw,
            session=session,
        )
        timeline = semantic_svc.apply_to_timeline(session, session_id, timeline)
        if session is not None and hasattr(self._timeline_read, "save"):
            self._timeline_read.save(session, timeline)
        now = datetime.now(timezone.utc)
        self._persistence.save(
            session,
            replace(s, status=EditorialTrainingSessionStatus.AWAITING_HUMAN, updated_at=now),
        )
        logger.info(
            "[EditorialTraining] timeline_submitted session=%s creative=%s scenes=%s",
            session_id,
            s.creative_id,
            len(timeline.timeline_scenes),
        )
        return timeline

    def apply_corrections(
        self,
        session: Any,
        session_id: str,
        items: tuple[EditorialTrainingCorrectionItem, ...],
    ) -> EditorialTrainingSession:
        self._require_enabled()
        s = self._get_or_raise(session, session_id)
        if s.status not in (
            EditorialTrainingSessionStatus.AWAITING_HUMAN,
            EditorialTrainingSessionStatus.READY,
            EditorialTrainingSessionStatus.DRAFT,
        ):
            raise ValueError("editorial_training_invalid_status_for_corrections")
        merged = tuple(s.corrections) + tuple(items)
        now = datetime.now(timezone.utc)
        hf = self._human_feedback
        if hf is not None and self._app_cfg.human_feedback_reinforcement.enabled:
            for it in items:
                rk = validate_correction_reward(it.reward)
                hf.ingest(
                    session,
                    IngestEditorialHumanFeedbackCommand(
                        event_kind=it.event_kind,
                        reward=rk,
                        creative_id=s.creative_id,
                        clip_id=it.clip_id,
                        replaced_clip_id=it.replaced_clip_id,
                        scene_index=it.scene_index,
                        narrative_function=it.narrative_function,
                        transition_type=it.transition_type,
                        query_fingerprint=None,
                    ),
                )
        out = replace(s, corrections=merged, updated_at=now)
        self._persistence.save(session, out)
        logger.info("[EditorialTraining] corrections_applied session=%s n=%s", session_id, len(items))
        return out

    def commit_learning(self, session: Any, session_id: str) -> EditorialTrainingSession:
        self._require_enabled()
        s = self._get_or_raise(session, session_id)
        if s.status != EditorialTrainingSessionStatus.AWAITING_HUMAN:
            raise ValueError("editorial_training_commit_requires_awaiting_human")
        tl = self._timeline_read.get_by_creative_id(session, s.creative_id)
        if tl is not None:
            self._style_embedding_attach.attach_if_configured(session, tl)
        now = datetime.now(timezone.utc)
        out = replace(s, status=EditorialTrainingSessionStatus.COMMITTED, updated_at=now)
        self._persistence.save(session, out)
        logger.info("[EditorialTraining] learning_committed session=%s creative=%s", session_id, s.creative_id)
        return out
