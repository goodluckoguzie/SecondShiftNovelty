import { shortWhen } from "../labels.js";

export function WatchList({ flags, onOpenQuote, onOpenWatch, compact }) {
  if (!flags?.length) return null;

  return (
    <div className="watch-list">
      <p className="watch-list__label">To watch</p>
      <ol>
        {flags.map((flag, index) => (
          <li key={flag.id || flag.message} className="watch-list__item">
            <span className="watch-list__num" aria-hidden>
              {index + 1}
            </span>
            <div className="min-w-0 flex-1">
              {compact || !flag.evidence?.length ? (
                <p className="leading-relaxed">{flag.message}</p>
              ) : (
                <details>
                  <summary className="cursor-pointer leading-relaxed">{flag.message}</summary>
                  <div className="mt-2 space-y-1">
                    {flag.evidence.slice(0, 3).map((event) => (
                      <button
                        key={event.id}
                        type="button"
                        className="block text-left text-accent underline"
                        onClick={() => onOpenQuote(event)}
                      >
                        {shortWhen(event.event_time)}
                      </button>
                    ))}
                    {flag.evidence.length > 3 && (
                      <p className="text-sm text-muted">and {flag.evidence.length - 3} more in History</p>
                    )}
                  </div>
                </details>
              )}
            </div>
          </li>
        ))}
      </ol>
      {compact && onOpenWatch && flags.length > 0 && (
        <button type="button" className="mt-3 font-bold text-accent underline" onClick={onOpenWatch}>
          Open Watch
        </button>
      )}
    </div>
  );
}
