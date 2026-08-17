import { useState } from "react";
import { eventLabel, joinCopy, sentence } from "../labels.js";

function dayHeading(iso) {
  const date = new Date(iso);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  const sameDay = (a, b) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  if (sameDay(date, today)) return "Today";
  if (sameDay(date, yesterday)) return "Yesterday";
  return date.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" });
}

function groupByDay(events) {
  const groups = [];
  for (const event of events) {
    const heading = dayHeading(event.event_time);
    const last = groups[groups.length - 1];
    if (last && last.heading === heading) last.items.push(event);
    else groups.push({ heading, items: [event] });
  }
  return groups;
}

export function TimelineScreen({ events, onOpenQuote }) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? events : (events || []).slice(0, 8);

  if (!events.length) {
    return (
      <section className="space-y-3">
        <h3 className="text-xl font-bold">History</h3>
        <p className="text-base text-muted">Nothing logged yet.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <h3 className="text-xl font-bold">History</h3>

      {groupByDay(visible).map((group) => (
        <div key={group.heading}>
          <h4 className="text-lg font-bold">{group.heading}</h4>
          <ul className="mt-1 divide-y divide-line border-y border-line bg-paper">
            {group.items.map((event) => (
              <li key={event.id} className="px-3 py-3">
                <p className="text-sm text-muted">
                  {joinCopy(
                    new Date(event.event_time).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }),
                    eventLabel(event.type, event.subtype),
                    event.logger_label,
                  )}
                </p>
                <p className="mt-1 text-base leading-relaxed">{sentence(event.detail)}</p>
                {event.raw_transcript && (
                  <button type="button" className="mt-1 font-bold text-accent underline" onClick={() => onOpenQuote(event)}>
                    See what was said
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}

      {!showAll && events.length > 8 && (
        <button type="button" className="font-bold text-accent underline" onClick={() => setShowAll(true)}>
          Show all {events.length} logs
        </button>
      )}
    </section>
  );
}
