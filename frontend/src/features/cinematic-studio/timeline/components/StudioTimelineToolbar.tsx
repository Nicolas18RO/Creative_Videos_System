type Props = {
  syncing: boolean;
  selectedSceneIndex: number | null;
  sceneCount: number;
  zoom: number;
  onZoomChange: (z: number) => void;
  onMergeWithNext: () => void;
  onReload: () => void;
};

export function StudioTimelineToolbar({
  syncing,
  selectedSceneIndex,
  sceneCount,
  zoom,
  onZoomChange,
  onMergeWithNext,
  onReload,
}: Props) {
  const canMerge =
    selectedSceneIndex !== null &&
    selectedSceneIndex >= 0 &&
    selectedSceneIndex < sceneCount - 1;

  return (
    <div className="cs-tl-toolbar">
      <h2 className="cs-tl-toolbar__title">Timeline Engine</h2>
      <div className="cs-tl-toolbar__actions">
        <label className="cs-tl-toolbar__zoom">
          Zoom
          <input
            type="range"
            min={0.6}
            max={2.5}
            step={0.1}
            value={zoom}
            disabled={syncing}
            onChange={(e) => onZoomChange(Number(e.target.value))}
          />
        </label>
        <button type="button" className="cs-btn cs-btn--ghost" disabled={syncing} onClick={onReload}>
          Recargar
        </button>
        <button
          type="button"
          className="cs-btn"
          disabled={!canMerge || syncing}
          onClick={onMergeWithNext}
          title="Fusionar escena seleccionada con la siguiente"
        >
          Fusionar con siguiente
        </button>
      </div>
    </div>
  );
}
