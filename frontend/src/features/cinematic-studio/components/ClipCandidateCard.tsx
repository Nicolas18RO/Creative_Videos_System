import type { ClipCandidateView } from "../presentation/studioScenePresentation";

type Props = {
  candidate: ClipCandidateView;
  allowFeedback: boolean;
  onAccept?: () => void;
  onReject?: () => void;
  disabled?: boolean;
};

export function ClipCandidateCard({ candidate, allowFeedback, onAccept, onReject, disabled }: Props) {
  const pathShort =
    candidate.clipPath.length > 42 ? `${candidate.clipPath.slice(0, 42)}…` : candidate.clipPath;

  return (
    <article
      className={`cs-clip-card${candidate.isSelectedOnTimeline ? " cs-clip-card--selected" : ""}${
        candidate.accepted === true ? " cs-clip-card--accepted" : ""
      }${candidate.accepted === false ? " cs-clip-card--rejected" : ""}`}
    >
      <div className="cs-clip-card__thumb-wrap">
        <img
          className="cs-clip-card__thumb"
          src={candidate.thumbnailUrl}
          alt=""
          loading="lazy"
          onError={(e) => {
            const img = e.target as HTMLImageElement;
            img.style.display = "none";
            const wrap = img.parentElement;
            if (wrap) wrap.classList.add("cs-clip-card__thumb-wrap--missing");
          }}
        />
        <span className="cs-clip-card__thumb-fallback">Sin miniatura</span>
      </div>
      <div className="cs-clip-card__meta">
        <span className="cs-clip-card__rank">Rank {candidate.rank}</span>
        <span className="cs-clip-card__score">{candidate.finalScore.toFixed(2)}</span>
        <span className="cs-clip-card__sim">sim {candidate.similarityScore.toFixed(2)}</span>
      </div>
      <p className="cs-clip-card__path" title={candidate.clipPath}>
        {pathShort}
      </p>
      {candidate.isSelectedOnTimeline && <span className="cs-clip-card__badge">En timeline</span>}
      {allowFeedback && (
        <div className="cs-clip-card__actions">
          <button type="button" className="cs-btn cs-btn--accept" disabled={disabled} onClick={onAccept}>
            Aceptar
          </button>
          <button type="button" className="cs-btn cs-btn--reject" disabled={disabled} onClick={onReject}>
            Rechazar
          </button>
        </div>
      )}
    </article>
  );
}
