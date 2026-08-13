import { useMemo, useState } from "react";
import { PageHeader } from "../components/PageHeader.jsx";
import { eventLabel, sentence } from "../labels.js";

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
  const [filter, setFilter] = useState("all");
  const [showAll, setShowAll] = useState(false);

  const filtered = useMemo(() => {
    if (filter === "all") return events;
    return events.filter((event) => event.type === filter);
  }, [events, filter]);

  const visible = showAll ? filtered : filtered.slice(0, 8);

  if (!events.length) {
    return (
      <section className="space-y-3">
        <PageHeader title="History" hint="Nothing logged yet." />
      </section>
    );
  }

  return (
    <section className="space-y-5">
      <PageHeader title="History" hint={`${filtered.length} log${filtered.length === 1 ? "" : "s"}.`} />

      <label className="block">
        <span className="mb-2 block font-bold">Show</span>
        <select className="nhs-select" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All logs</option>
          <option value="medication">Medicines</option>
          <option value="symptom">Symptoms</option>
          <option value="meal">Meals</option>
          <option value="mood">Mood</option>
        </select>
      </label>

      {groupByDay(visible).map((group) => (
        <div key={group.heading}>
          <h3 className="text-lg font-bold">{group.heading}</h3>
          <ul className="mt-1 divide-y divide-line border-y border-line bg-paper">
            {group.items.map((event) => (
              <li key={event.id} className="px-3 py-3">
                <p className="text-sm text-muted">
                  {new Date(event.event_time).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}
                  {" · "}
                  {eventLabel(event.type, event.subtype)}
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

      {!showAll && filtered.length > 8 && (
        <button type="button" className="font-bold text-accent underline" onClick={() => setShowAll(true)}>
          Show all {filtered.length} logs
        </button>
      )}
    </section>
  );
}
