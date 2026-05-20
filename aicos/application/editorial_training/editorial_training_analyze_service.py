"""Orquestación del análisis automático para el workspace de entrenamiento editorial."""

from __future__ import annotations

import logging
from typing import Any

from aicos.application.editorial_training.analyzed_scene_to_timeline import map_analyzed_scenes_to_raw_inputs
from aicos.application.editorial_training.editorial_training_workspace_service import EditorialTrainingWorkspaceService
from aicos.config import EditorialTrainingWorkspaceConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline
from aicos.domain.editorial_training.entities import EditorialTrainingSessionStatus
from aicos.models.schemas import AnalyzeAPIResponse

logger = logging.getLogger(__name__)


class EditorialTrainingAnalyzeService:
    """Ejecuta ``analyze_audio`` y persiste timeline vía ``EditorialTrainingWorkspaceService``."""

    def __init__(
        self,
        *,
        workspace: EditorialTrainingWorkspaceService,
        workspace_cfg: EditorialTrainingWorkspaceConfig,
    ) -> None:
        self._workspace = workspace
        self._cfg = workspace_cfg

    def _maybe_generate_visual_previews(self, session: Any, creative_id: str) -> None:
        from aicos.config import get_config

        app = get_config()
        if not app.timeline_visualization.enabled or not app.timeline_visualization.auto_generate_after_analyze:
            return
        try:
            from aicos.services.timeline_visualization_factory import build_timeline_visualization_service

            viz = build_timeline_visualization_service(app)
            viz.generate_previews(session, creative_id)
        except Exception:
            logger.exception("[EditorialTraining] visual_preview_generation_failed creative=%s", creative_id)

    async def run(self, session: Any, session_id: str) -> tuple[CreativeTimeline, AnalyzeAPIResponse]:
        from aicos.modules.script_analyzer import analyze_audio

        s = self._workspace.get_session(session, session_id)
        if s is None:
            raise ValueError("editorial_training_session_not_found")
        if not s.audio_path.strip():
            raise ValueError("editorial_training_audio_required")
        if not s.final_video_path.strip():
            raise ValueError("editorial_training_video_required")
        if s.status not in (
            EditorialTrainingSessionStatus.DRAFT,
            EditorialTrainingSessionStatus.READY,
            EditorialTrainingSessionStatus.AWAITING_HUMAN,
            EditorialTrainingSessionStatus.FAILED,
        ):
            raise ValueError("editorial_training_invalid_status_for_analyze")

        self._workspace.update_session_status(session, session_id, EditorialTrainingSessionStatus.ANALYZING)
        try:
            resp = await analyze_audio(
                s.audio_path,
                project_name=(s.project_label or s.creative_label or "AICOS Training").strip() or "AICOS Training",
                product_category=(s.product_category or "general").strip() or "general",
                target_audience="adultos 35-55",
                include_clip_search=bool(self._cfg.analyze_include_clip_search),
                enable_intelligence=bool(self._cfg.analyze_enable_intelligence),
            )
            raw = map_analyzed_scenes_to_raw_inputs(resp.scenes)
            if not raw:
                raise ValueError("editorial_training_analyze_empty_scenes")
            from aicos.services.editorial_semantic_intent_factory import build_editorial_semantic_intent_service

            build_editorial_semantic_intent_service().seed_from_analysis(session, session_id, resp.scenes)
            timeline = self._workspace.submit_timeline(
                session,
                session_id,
                raw,
                from_auto_detection=True,
            )
            self._maybe_generate_visual_previews(session, timeline.creative_id)
            logger.info(
                "[EditorialTraining] analyze_done session=%s scenes=%s warning=%s",
                session_id,
                len(timeline.timeline_scenes),
                bool(resp.warning),
            )
            return timeline, resp
        except Exception:
            self._workspace.update_session_status(session, session_id, EditorialTrainingSessionStatus.FAILED)
            raise
