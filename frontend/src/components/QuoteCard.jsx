import { shortWhen } from "../labels.js";

export function QuoteCard({ quote, onClose }) {
  if (!quote) return null;
  return (
    <aside className="nhs-inset">
      <div className="flex items-start justify-between gap-3">
        <p className="font-bold">What was said</p>
        <button type="button" className="font-bold text-accent underline" onClick={onClose}>
          Close
        </button>
      </div>
      <p className="mt-2 text-lg leading-snug">“{quote.raw_transcript || quote.detail}”</p>
      <p className="mt-1 text-sm text-muted">{shortWhen(quote.event_time)}</p>
    </aside>
  );
}
