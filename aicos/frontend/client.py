"""Cliente HTTP hacia la FastAPI local (presentación → API, sin importar core/modules)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AicosApiClient:
    """Fachada mínima para el dashboard PyQt6 (solo lectura / operaciones vía API)."""

    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        return self._base

    def set_base_url(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self._base, timeout=self._timeout)

    def list_projects(self) -> list[dict[str, Any]]:
        with self._client() as c:
            r = c.get("/projects")
            r.raise_for_status()
            return list(r.json())

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self._client() as c:
            r = c.get(f"/projects/{project_id}")
            r.raise_for_status()
            return dict(r.json())

    def get_gaps(self, project_id: str) -> dict[str, Any]:
        with self._client() as c:
            r = c.get(f"/gaps/{project_id}")
            r.raise_for_status()
            return dict(r.json())

    def get_library_stats(self) -> dict[str, Any]:
        with self._client() as c:
            r = c.get("/library/stats")
            r.raise_for_status()
            return dict(r.json())

    def get_clips(self, *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """GET /library/clips — paginación; seguro para usar desde ``JsonTaskThread``."""
        with self._client() as c:
            r = c.get("/library/clips", params={"limit": limit, "offset": offset})
            r.raise_for_status()
            return dict(r.json())

    def post_search(self, body: dict[str, Any]) -> dict[str, Any]:
        with self._client() as c:
            r = c.post("/search", json=body)
            r.raise_for_status()
            return dict(r.json())

    def post_feedback(self, body: dict[str, Any]) -> dict[str, Any]:
        with self._client() as c:
            r = c.post("/feedback", json=body)
            r.raise_for_status()
            return dict(r.json())

    def post_analyze(self, body: dict[str, Any]) -> dict[str, Any]:
        """POST /analyze (puede tardar varios minutos según audio)."""
        with self._client() as c:
            r = c.post("/analyze", json=body)
            r.raise_for_status()
            return dict(r.json())

    def analyze_audio(
        self,
        audio_path: str,
        *,
        project_name: str = "Proyecto",
        persist: bool = True,
        include_clip_search: bool = True,
        enable_intelligence: bool = True,
        product_category: str = "salud/bienestar",
        target_audience: str = "adultos 35-55",
        product_name: str | None = None,
        gender_hint_default: str | None = None,
    ) -> dict[str, Any]:
        """Atajo tipado hacia ``POST /analyze`` (misma semántica que ``post_analyze``)."""
        body: dict[str, Any] = {
            "audio_path": audio_path,
            "project_name": project_name,
            "persist": persist,
            "include_clip_search": include_clip_search,
            "enable_intelligence": enable_intelligence,
            "product_category": product_category,
            "target_audience": target_audience,
        }
        if product_name is not None:
            body["product_name"] = product_name
        if gender_hint_default is not None:
            body["gender_hint_default"] = gender_hint_default
        return self.post_analyze(body)

    def get_insights_summary(self, *, refresh: bool = False) -> dict[str, Any]:
        with self._client() as c:
            r = c.get("/insights/summary", params={"refresh": refresh})
            r.raise_for_status()
            return dict(r.json())

    def get_insights_gaps(self, *, refresh: bool = False) -> dict[str, Any]:
        with self._client() as c:
            r = c.get("/insights/gaps", params={"refresh": refresh})
            r.raise_for_status()
            return dict(r.json())

    def get_insights_trends(self, *, refresh: bool = False) -> dict[str, Any]:
        with self._client() as c:
            r = c.get("/insights/trends", params={"refresh": refresh})
            r.raise_for_status()
            return dict(r.json())

    def get_decisions_summary(self, *, refresh: bool = False) -> dict[str, Any]:
        with self._client() as c:
            r = c.get("/decisions/summary", params={"refresh": refresh})
            r.raise_for_status()
            return dict(r.json())

    def get_decisions_list(
        self,
        *,
        limit: int = 80,
        offset: int = 0,
        decision_type: str | None = None,
        severity: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset, "refresh": refresh}
        if decision_type:
            params["decision_type"] = decision_type
        if severity:
            params["severity"] = severity
        with self._client() as c:
            r = c.get("/decisions/list", params=params)
            r.raise_for_status()
            return dict(r.json())

    def get_decisions_impact(self, *, refresh: bool = False) -> dict[str, Any]:
        with self._client() as c:
            r = c.get("/decisions/impact", params={"refresh": refresh})
            r.raise_for_status()
            return dict(r.json())

    def get_hooks_search(self, q: str, *, n_results: int = 8, candidate_pool_size: int = 24) -> dict[str, Any]:
        with self._client() as c:
            r = c.get(
                "/hooks/search",
                params={"q": q, "n_results": n_results, "candidate_pool_size": candidate_pool_size},
            )
            r.raise_for_status()
            return dict(r.json())

    def get_benchmark_phase3(self, *, k: int = 5, max_cases: int = 80) -> dict[str, Any]:
        with self._client() as c:
            r = c.get("/benchmark/phase3", params={"k": k, "max_cases": max_cases})
            r.raise_for_status()
            return dict(r.json())

    def post_taxonomy_reclassify_batch(self, body: dict[str, Any]) -> dict[str, Any]:
        with self._client() as c:
            r = c.post("/taxonomy/reclassify/batch", json=body)
            r.raise_for_status()
            return dict(r.json())
