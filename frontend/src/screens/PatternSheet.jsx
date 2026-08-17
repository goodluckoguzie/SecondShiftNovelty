import { Press } from "../components/Press.jsx";
import { eventFacts, eventLabel, shortWhen } from "../labels.js";

export function PatternSheet({ hit, onOpen, onStay, onOpenQuote }) {
  if (!hit) return null;
  const quotes = hit.similar?.length ? hit.similar : hit.last ? [hit.last] : [];
  const title = hit.personName ? `Saved for ${hit.personName}` : "Saved";
  const claim = hit.flag?.message || "This has happened before.";
  const happenedLastWeek = Boolean(quotes.length);

  return (
    <div className="speak-overlay" role="dialog" aria-modal="true" aria-label="This happened last week">
      <div className="speak-sheet">
        <h2 className="text-2xl font-bold">{title}</h2>
        <p className="mt-2 text-lg font-bold">{happenedLastWeek ? "This happened last week too." : claim}</p>
        <p className="mt-2 text-base leading-relaxed">{claim}</p>
        <p className="mt-2 text-sm text-muted">A rules engine counted this. It is not a diagnosis.</p>

        {hit.today ? (
          <div className="mt-4">
            <p className="text-sm font-bold">Tonight</p>
            {eventFacts(hit.today) ? <p className="mt-1 text-base">{eventFacts(hit.today)}</p> : null}
            <p className="mt-1 text-base">{hit.today.detail || hit.today.raw_transcript}</p>
          </div>
        ) : null}

        {quotes.length ? (
          <ul className="mt-4 divide-y divide-line border-y border-line">
            {quotes.map((event) => (
              <li key={event.id || event.event_time} className="py-3">
                <p className="text-sm text-muted">
                  {shortWhen(event.event_time)}
                  {event.logger_label ? `, ${event.logger_label}` : ""}
                  {event.subtype ? `, ${eventLabel(event.type, event.subtype)}` : ""}
                </p>
                {eventFacts(event) ? <p className="mt-1 text-sm text-muted">{eventFacts(event)}</p> : null}
                <p className="mt-1 text-base">{event.detail || event.raw_transcript}</p>
                {event.raw_transcript && onOpenQuote ? (
                  <button type="button" className="mt-1 font-bold text-accent underline" onClick={() => onOpenQuote(event)}>
                    See what was said
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}

        <div className="mt-6 space-y-3">
          {hit.personId ? (
            <Press tone="primary" onClick={() => onOpen({ id: hit.personId, name: hit.personName })}>
              Open {hit.personName || "them"}
            </Press>
          ) : null}
          <Press tone="secondary" onClick={onStay}>
            Stay on the wing
          </Press>
        </div>
      </div>
    </div>
  );
}
