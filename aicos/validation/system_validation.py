"""Validación end-to-end del núcleo AICOS (solo lectura).

Ejecutar::

    python -m aicos.validation.system_validation
    python -m aicos.validation.system_validation -v
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.database.db import ClipRow, get_engine, session_scope
from aicos.models.schemas import SearchRequest
from aicos.modules.clip_recommender import recommend
from aicos.taxonomy import constants as taxonomy_constants

logger = logging.getLogger(__name__)

PERF_TARGET_MS = 500.0


def _normalize_embedding_list(raw: Any) -> list[Any]:
    """Chroma puede devolver lista de vectores o ndarray 2D; evita ``or`` sobre ndarray."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return list(raw)
    shape = getattr(raw, "shape", None)
    if shape is not None:
        try:
            if len(shape) == 1:
                return [raw]
            if len(shape) >= 2:
                n = int(shape[0])
                return [raw[i] for i in range(n)]
        except (TypeError, ValueError, IndexError):
            return [raw]
    return [raw]


SEARCH_QUERIES: tuple[str, ...] = ("back pain", "knee injury", "muscle tension")

# Marcadores en metadatos/rutas que suelen ser irrelevantes para consultas clínicas/musculares.
_UNRELATED_LEXICAL_MARKERS: frozenset[str] = frozenset(
    {"vehicle", "engine", "automotive", "driving", "beverage", "computer", "sanitary_towel"}
)


def _vec_len(emb: Any) -> int:
    """Longitud de vector (lista o ndarray 1D)."""
    if emb is None:
        return 0
    try:
        return int(len(emb))
    except TypeError:
        return 0


@dataclass
class ValidationReport:
    """Resumen de integridad del sistema (compatible con JSON)."""

    database_ok: bool
    vector_db_ok: bool
    duplicates_found: int
    embedding_consistency_ok: bool
    taxonomy_ok: bool
    search_quality_ok: bool
    performance_ok: bool
    overall_status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_summary_dict(self) -> dict[str, Any]:
        """Diccionario con solo los campos del contrato de salida principal."""
        return {
            "database_ok": self.database_ok,
            "vector_db_ok": self.vector_db_ok,
            "duplicates_found": self.duplicates_found,
            "embedding_consistency_ok": self.embedding_consistency_ok,
            "taxonomy_ok": self.taxonomy_ok,
            "search_quality_ok": self.search_quality_ok,
            "performance_ok": self.performance_ok,
            "overall_status": self.overall_status,
        }


def _validate_sqlite() -> tuple[bool, dict[str, Any]]:
    """1) SQLite: conteo, integridad, session_scope (solo SELECT / PRAGMA)."""
    out: dict[str, Any] = {}
    ok = True
    try:
        eng = get_engine()
        with eng.connect() as conn:
            t0 = time.perf_counter()
            rows = conn.execute(text("PRAGMA integrity_check")).fetchall()
            out["integrity_check_ms"] = (time.perf_counter() - t0) * 1000.0
            out["integrity_check"] = [str(r[0]) for r in rows][:5]
            if not rows or str(rows[0][0]).upper() != "OK":
                ok = False
                logger.error("PRAGMA integrity_check falló: %s", rows)
    except Exception as e:
        ok = False
        out["error"] = str(e)
        logger.exception("Validación SQLite (integridad) falló")

    clip_count = 0
    session_ok = False
    count_ms = 0.0
    try:
        with session_scope() as session:
            session_ok = True
            t_count = time.perf_counter()
            clip_count = int(session.execute(select(func.count()).select_from(ClipRow)).scalar_one())
            count_ms = (time.perf_counter() - t_count) * 1000.0
        out["clip_count"] = clip_count
        out["session_scope_ok"] = session_ok
        out["clip_count_query_ms"] = round(count_ms, 3)
        out["db_query_ms"] = float(out.get("integrity_check_ms", 0.0)) + count_ms
    except Exception as e:
        ok = False
        out["session_error"] = str(e)
        logger.exception("session_scope / conteo ClipRow falló")

    if clip_count == 0:
        out["warning"] = "Base sin clips indexados"
        logger.warning("ClipRow count=0")

    return ok and session_ok, out


def _validate_duplicate_hashes(session: Session) -> tuple[int, dict[str, Any]]:
    """2) Duplicados físicos por file_hash (misma huella, varias rutas)."""
    details: dict[str, Any] = {}
    subq = (
        select(ClipRow.file_hash, func.count().label("cnt"))
        .where(ClipRow.file_hash.is_not(None))
        .where(ClipRow.file_hash != "")
        .group_by(ClipRow.file_hash)
        .having(func.count() > 1)
    )
    rows = session.execute(subq).all()
    duplicate_extra_rows = 0
    groups: list[dict[str, Any]] = []
    for file_hash, cnt in rows:
        n = int(cnt)
        duplicate_extra_rows += n - 1
        groups.append({"file_hash": (file_hash or "")[:16] + "…", "count": n})
    details["hash_collision_groups"] = len(rows)
    details["sample_groups"] = groups[:10]
    return duplicate_extra_rows, details


def _validate_chroma(expected_clip_count: int) -> tuple[bool, dict[str, Any]]:
    """3) Chroma: colección, conteo, embeddings no vacíos."""
    out: dict[str, Any] = {}
    ok = True
    try:
        store = VectorStore()
        col = store.collection
        out["collection_name"] = store.collection_name
        out["persist_path"] = str(store._path)
        count = int(col.count())
        out["chroma_count"] = count
        if count == 0 and expected_clip_count > 0:
            ok = False
            logger.error("Chroma vacío pero hay clips en SQLite")
        peek_limit = min(3, count) if count > 0 else 1
        peek = col.get(limit=peek_limit, include=["embeddings"]) if count > 0 else {}
        embs = _normalize_embedding_list(peek.get("embeddings"))
        if count > 0:
            if not embs or _vec_len(embs[0]) == 0:
                ok = False
                out["embedding_peek_error"] = "Sin embeddings en muestra"
                logger.error("Chroma: embeddings vacíos en peek")
            else:
                out["peek_embedding_dim"] = _vec_len(embs[0])
        if expected_clip_count > 0:
            tol = max(1, int(expected_clip_count * 0.02))
            if abs(count - expected_clip_count) > tol:
                ok = False
                out["count_mismatch"] = {
                    "sqlite_clips": expected_clip_count,
                    "chroma_count": count,
                    "tolerance": tol,
                }
                logger.error(
                    "Chroma count (%s) no coincide con SQLite (%s) fuera de tolerancia (%s)",
                    count,
                    expected_clip_count,
                    tol,
                )
    except Exception as e:
        ok = False
        out["error"] = str(e)
        logger.exception("Validación Chroma falló")

    return ok, out


def _validate_embedding_consistency(
    session: Session, store: VectorStore, *, sample_size: int = 5
) -> tuple[bool, dict[str, Any]]:
    """4) Muestra aleatoria: vectores en Chroma y dimensión uniforme."""
    details: dict[str, Any] = {"samples": []}
    ids = list(session.scalars(select(ClipRow.id)).all())
    if not ids:
        details["skipped"] = "Sin clips"
        return True, details

    sample = random.sample(ids, k=min(sample_size, len(ids)))
    col = store.collection
    got = col.get(ids=sample, include=["embeddings"])
    got_ids = got.get("ids") or []
    embs = _normalize_embedding_list(got.get("embeddings"))
    dims: list[int] = []
    ok = True
    for cid, emb in zip(got_ids, embs, strict=False):
        if emb is None or _vec_len(emb) == 0:
            ok = False
            details["samples"].append({"clip_id": cid, "ok": False, "reason": "sin embedding"})
            continue
        d = _vec_len(emb)
        dims.append(d)
        details["samples"].append({"clip_id": cid, "ok": True, "dim": d})
    if dims and len(set(dims)) != 1:
        ok = False
        details["dimension_mismatch"] = list(set(dims))
        logger.error("Dimensiones de embedding inconsistentes: %s", dims)
    if len(got_ids) != len(sample):
        missing = set(sample) - set(got_ids)
        if missing:
            ok = False
            details["missing_ids_in_chroma"] = list(missing)[:10]
            logger.error("IDs no encontrados en Chroma: %s", list(missing)[:5])
    details["dims_observed"] = dims
    return ok, details


def _validate_taxonomy() -> tuple[bool, dict[str, Any]]:
    """5) Constantes de taxonomía: conjuntos no vacíos, expansiones coherentes."""
    details: dict[str, Any] = {}
    ok = True
    issues: list[str] = []

    if not taxonomy_constants.NARRATIVE_FUNCTIONS:
        issues.append("NARRATIVE_FUNCTIONS vacío")
        ok = False
    if not taxonomy_constants.GENDER_PREFIXES:
        issues.append("GENDER_PREFIXES vacío")
        ok = False
    if not taxonomy_constants.KNOWN_SUBCATEGORIES:
        issues.append("KNOWN_SUBCATEGORIES vacío")
        ok = False

    for nf, exp in taxonomy_constants.NARRATIVE_EXPANSIONS.items():
        if nf not in taxonomy_constants.NARRATIVE_FUNCTIONS:
            issues.append(f"NARRATIVE_EXPANSIONS clave desconocida: {nf}")
            ok = False
        if not (exp or "").strip():
            issues.append(f"NARRATIVE_EXPANSIONS vacío para {nf}")
            ok = False

    for sub, exp in taxonomy_constants.SUBCATEGORY_EXPANSIONS.items():
        if not (exp or "").strip():
            issues.append(f"SUBCATEGORY_EXPANSIONS vacío para {sub}")
            ok = False

    if "" in taxonomy_constants.NARRATIVE_FUNCTIONS or "" in taxonomy_constants.GENDER_PREFIXES:
        issues.append("Entrada vacía en conjuntos de taxonomía")
        ok = False

    details["issues"] = issues[:50]
    return ok, details


def _tokens(q: str) -> set[str]:
    return {t.lower() for t in re.findall(r"\w+", q) if len(t) > 2}


def _haystack_from_meta(meta: dict[str, Any]) -> str:
    parts = [
        str(meta.get("semantic_text") or ""),
        str(meta.get("relative_path") or ""),
        str(meta.get("absolute_path") or ""),
        str(meta.get("subcategory") or ""),
        str(meta.get("narrative_function") or ""),
        str(meta.get("context") or ""),
    ]
    return " ".join(parts).lower()


def _meta_seems_unrelated_to_health_query(query: str, meta: dict[str, Any]) -> bool:
    """Heurística: consultas de dolor/músculo vs metadatos claramente no clínicos."""
    q = query.lower()
    if not any(k in q for k in ("pain", "injury", "muscle", "tension", "knee", "back")):
        return False
    h = _haystack_from_meta(meta)
    return any(m in h for m in _UNRELATED_LEXICAL_MARKERS)


def _search_relevance_score(query: str, meta: dict[str, Any]) -> int:
    toks = _tokens(query)
    if not toks:
        return 0
    h = _haystack_from_meta(meta)
    return sum(1 for t in toks if t in h)


def _query_text_for_search(req: SearchRequest) -> str:
    """Misma construcción que clip_recommender._build_query_text (API real)."""
    nf = (req.narrative_function or "PROBLEM").upper()
    expansion = taxonomy_constants.NARRATIVE_EXPANSIONS.get(nf, nf.lower())
    return f"{expansion} {req.query}".strip()


def _validate_search_and_performance(
    embedder: Embedder, store: VectorStore, *, perf_db_ms: float
) -> tuple[bool, bool, dict[str, Any]]:
    """6) Búsqueda vía ``recommend`` (misma capa que ``api.routers.search``); 7) tiempos."""
    search_details: dict[str, Any] = {"queries": [], "api_search_module": None}
    search_ok = True
    col = store.collection

    try:
        from aicos.api.routers import search as api_search

        _search_fn = getattr(api_search, "search", None)
        if _search_fn is None:
            search_details["api_import_error"] = "router sin función search"
            return False, False, search_details
        search_details["api_router_search"] = getattr(_search_fn, "__qualname__", "search")
    except Exception as e:
        search_ok = False
        search_details["api_import_error"] = str(e)
        logger.exception("No se pudo importar aicos.api.routers.search")
        return False, False, search_details

    t_vec_start = time.perf_counter()
    per_query_ms: list[float] = []
    try:
        for q in SEARCH_QUERIES:
            t0 = time.perf_counter()
            req = SearchRequest(query=q, n_results=5, candidate_pool_size=20)
            resp = recommend(req, embedder, store)
            per_query_ms.append((time.perf_counter() - t0) * 1000.0)
            top = resp.results[:5]
            ids = [r.clip_id for r in top if r.clip_id]
            meta_by_id: dict[str, dict[str, Any]] = {}
            if ids:
                got = col.get(ids=ids, include=["metadatas"])
                for cid, m in zip(got.get("ids") or [], got.get("metadatas") or []):
                    if cid and isinstance(m, dict):
                        meta_by_id[str(cid)] = m

            scores: list[int] = []
            for r in top:
                meta = meta_by_id.get(r.clip_id, {})
                if not meta:
                    meta = {
                        "semantic_text": "",
                        "relative_path": r.clip_path or "",
                        "absolute_path": r.clip_path or "",
                        "subcategory": "",
                        "narrative_function": r.narrative_function or "",
                    }
                scores.append(_search_relevance_score(q, meta))

            best_overlap = max(scores) if scores else 0
            best_sim = max((r.final_score for r in top), default=0.0)
            metas_for_top: list[dict[str, Any]] = []
            for r in top:
                m = meta_by_id.get(r.clip_id, {})
                if not m:
                    m = {
                        "semantic_text": "",
                        "relative_path": r.clip_path or "",
                        "absolute_path": r.clip_path or "",
                        "subcategory": "",
                        "narrative_function": r.narrative_function or "",
                    }
                metas_for_top.append(m)
            unrelated_in_top3 = sum(
                1 for m in metas_for_top[:3] if _meta_seems_unrelated_to_health_query(q, m)
            )
            row = {
                "query": q,
                "results": len(top),
                "is_gap": resp.is_gap,
                "best_token_overlap": best_overlap,
                "best_final_score": round(best_sim, 4),
                "unrelated_hits_in_top3": unrelated_in_top3,
            }
            if not top:
                row["ok"] = False
                search_ok = False
            elif unrelated_in_top3 >= 3:
                row["ok"] = False
                search_ok = False
                row["reason"] = "top3 dominado por categorías no relacionadas (heurística)"
            elif best_overlap == 0 and best_sim < 0.2:
                row["ok"] = False
                search_ok = False
                row["reason"] = "sin solapamiento léxico y score bajo"
            else:
                row["ok"] = True
            search_details["queries"].append(row)

        t_one = time.perf_counter()
        probe = SearchRequest(query="mobility pain", n_results=3, candidate_pool_size=10)
        qvec = embedder.embed(_query_text_for_search(probe))
        _, _, _ = store.query(qvec, n_results=3)
        per_query_ms.append((time.perf_counter() - t_one) * 1000.0)
        search_details["raw_vector_query_ms"] = round(per_query_ms[-1], 2)
    except Exception as e:
        search_ok = False
        search_details["error"] = str(e)
        logger.exception("Validación de búsqueda falló")

    vector_ms = (time.perf_counter() - t_vec_start) * 1000.0
    search_details["vector_search_total_ms"] = round(vector_ms, 2)
    search_details["recommend_calls_ms"] = [round(x, 2) for x in per_query_ms[: len(SEARCH_QUERIES)]]
    search_details["perf_db_ms_recorded"] = round(perf_db_ms, 2)

    avg_recommend_ms = sum(per_query_ms[: len(SEARCH_QUERIES)]) / max(len(SEARCH_QUERIES), 1)
    raw_ms = per_query_ms[-1] if per_query_ms else 0.0
    perf_ok = perf_db_ms < PERF_TARGET_MS and avg_recommend_ms < PERF_TARGET_MS and raw_ms < PERF_TARGET_MS
    if not perf_ok:
        logger.warning(
            "Rendimiento por encima del objetivo (~%s ms): db=%.2f ms, total búsqueda=%.2f ms, avg recommend=%.2f ms",
            PERF_TARGET_MS,
            perf_db_ms,
            vector_ms,
            avg_recommend_ms,
        )

    return search_ok, perf_ok, search_details


def run_system_validation(*, seed: int | None = None) -> ValidationReport:
    """Ejecuta todas las validaciones (solo lectura) y devuelve el informe."""
    if seed is not None:
        random.seed(seed)

    report_details: dict[str, Any] = {}
    database_ok, db_part = _validate_sqlite()
    report_details["database"] = db_part
    perf_db_ms = float(db_part.get("db_query_ms") or 0.0)

    duplicates_found = 0
    dup_details: dict[str, Any] = {}
    clip_count = int(db_part.get("clip_count") or 0)

    vector_db_ok, chroma_details = _validate_chroma(clip_count)
    report_details["vector_store"] = chroma_details

    embedding_ok = True
    emb_details: dict[str, Any] = {}
    search_ok = True
    perf_ok = True
    search_perf_details: dict[str, Any] = {}

    taxonomy_ok, tax_details = _validate_taxonomy()
    report_details["taxonomy"] = tax_details

    if database_ok:
        try:
            with session_scope() as session:
                duplicates_found, dup_details = _validate_duplicate_hashes(session)
                report_details["duplicate_hashes"] = dup_details

                if clip_count > 0 and vector_db_ok:
                    try:
                        store = VectorStore()
                        embedding_ok, emb_details = _validate_embedding_consistency(session, store)
                        report_details["embedding_consistency"] = emb_details

                        embedder = Embedder()
                        search_ok, perf_ok, search_perf_details = _validate_search_and_performance(
                            embedder, store, perf_db_ms=perf_db_ms
                        )
                        report_details["search_and_performance"] = search_perf_details
                    except Exception as e:
                        embedding_ok = False
                        search_ok = False
                        perf_ok = False
                        report_details["embedding_search_error"] = str(e)
                        logger.exception("Embedding / búsqueda no disponibles")
        except Exception as e:
            database_ok = False
            report_details["session_batch_error"] = str(e)
            logger.exception("Error en bloque de validación con sesión")

    if clip_count == 0:
        if chroma_details.get("chroma_count", -1) not in (0, -1):
            vector_db_ok = False
            report_details["vector_store"]["empty_sqlite_mismatch"] = True
        embedding_ok = True
        search_ok = False
        perf_ok = perf_db_ms < PERF_TARGET_MS
        report_details["search_skipped"] = "Sin clips en SQLite"

    overall = "HEALTHY"
    if not database_ok or not vector_db_ok or not embedding_ok:
        overall = "FAILED"
    elif not taxonomy_ok or not search_ok or not perf_ok or clip_count == 0:
        overall = "DEGRADED"

    return ValidationReport(
        database_ok=database_ok,
        vector_db_ok=vector_db_ok,
        duplicates_found=duplicates_found,
        embedding_consistency_ok=embedding_ok,
        taxonomy_ok=taxonomy_ok,
        search_quality_ok=search_ok,
        performance_ok=perf_ok,
        overall_status=overall,
        details=report_details,
    )


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validación end-to-end AICOS (solo lectura).")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--json", action="store_true", help="Salida JSON (resumen + details)")
    parser.add_argument("--seed", type=int, default=None, help="Semilla para muestreo de embeddings")
    args = parser.parse_args(argv)

    _configure_logging(args.verbose)
    report = run_system_validation(seed=args.seed)

    summary = report.to_summary_dict()
    summary["details"] = report.details

    if args.json:
        sys.stdout.write(json.dumps(summary, indent=2, default=str) + "\n")
        sys.stdout.flush()
    else:
        logger.info("=== AICOS system validation ===")
        for k, v in report.to_summary_dict().items():
            logger.info("%s: %s", k, v)
        if report.details:
            logger.debug("Detalles: %s", json.dumps(report.details, default=str)[:8000])

    if report.overall_status == "HEALTHY":
        return 0
    if report.overall_status == "DEGRADED":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
