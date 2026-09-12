"""Reglas del pipeline de exportación (Phase 7.4)."""

from aicos.domain.export_pipeline.entities import ExportTimelineScene, ProjectEditorialBundle
from aicos.domain.export_pipeline.rules import (
    build_capcut_manifest,
    build_export_manifest,
    bundle_timeline_duration_ms,
    validate_bundle_for_export,
)


def _scene(idx: int, start: int, end: int, clip: str | None = "c1") -> ExportTimelineScene:
    return ExportTimelineScene(
        scene_id=f"s{idx}",
        scene_index=idx,
        start_ms=start,
        end_ms=end,
        duration_ms=end - start,
        text=f"text {idx}",
        concept="c",
        narrative_function="NATURAL",
        selected_clip_id=clip,
    )


def _bundle(scenes: tuple[ExportTimelineScene, ...]) -> ProjectEditorialBundle:
    return ProjectEditorialBundle(
        project_id="p1",
        project_name="Test",
        status="draft",
        audio_file_path="/tmp/audio.mp3",
        transcript_path=None,
        product_name=None,
        product_category=None,
        target_audience=None,
        scenes=scenes,
        assets=(),
    )


def test_bundle_timeline_duration():
    scenes = (_scene(0, 0, 5000), _scene(1, 5000, 12000))
    assert bundle_timeline_duration_ms(scenes) == 12000


def test_validate_bundle_ok():
    ok, msg = validate_bundle_for_export(_bundle((_scene(0, 0, 5000),)))
    assert ok and msg == "ok"


def test_validate_bundle_empty():
    ok, msg = validate_bundle_for_export(_bundle(()))
    assert not ok and msg == "timeline_empty"


def test_capcut_manifest_warnings_missing_clip():
    scenes = (_scene(0, 0, 5000, None),)
    manifest = build_capcut_manifest(_bundle(scenes), {})
    assert any("no_clip_selected" in w for w in manifest.warnings)


def test_export_manifest_missing_asset_flag():
    scenes = (_scene(0, 0, 5000, "missing"),)
    manifest = build_export_manifest(_bundle(scenes), {"missing": ""})
    assert manifest.missing_assets
