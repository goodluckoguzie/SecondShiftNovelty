import { useMemo, useState } from "react";
import { PageHeader } from "../components/PageHeader.jsx";
import { Press } from "../components/Press.jsx";
import { eventFacts, eventLabel, shortWhen, voiceLabel } from "../labels.js";
import { WeekChart } from "./PatternsScreen.jsx";
import { TimelineScreen } from "./TimelineScreen.jsx";

function pickFlag(flags, patternHit) {
  const list = flags || [];
  const want = patternHit?.today?.subtype || patternHit?.flag?.subtype;
  if (want) {
    const match = list.find((flag) => flag.subtype === want || (want === "vomiting" && flag.kind === "meal_then_symptom"));
    if (match) return match;
  }
  return (
    list.find((flag) => ["vomiting", "confusion", "not_himself", "hospital_return", "medication"].includes(flag.subtype)) ||
    list[0] ||
    null
  );
}

function proofQuotes(flag, patternHit) {
  const rows = [];
  const seen = new Set();
  function add(event) {
    if (!event) return;
    const key = event.id || `${event.event_time}-${event.raw_transcript}`;
    if (seen.has(key)) return;
    seen.add(key);
    rows.push(event);
  }
  if (patternHit?.today) add(patternHit.today);
  if (patternHit?.last) add(patternHit.last);
  (patternHit?.similar || []).forEach(add);
  (flag?.evidence || []).forEach(add);
  return rows.slice(0, 3);
}

export function PersonScreen({
  profile,
  events,
  flags,
  chart,
  patternHit,
  showPages,
  onOpenQuote,
  onBrief,
}) {
  const [showLogs, setShowLogs] = useState(false);
  const samePerson = patternHit && Number(patternHit.personId) === Number(profile?.id);
  const hit = samePerson ? patternHit : null;
  const flag = pickFlag(flags, hit);
  const quotes = useMemo(() => proofQuotes(flag, hit), [flag, hit]);
  const logCount = (events || []).length;

  return (
    <section className="space-y-5">
      <PageHeader
        title={profile?.name || "Person"}
        hint={profile?.age ? `Age ${profile.age}` : undefined}
      />

      {profile?.risks ? <p className="text-lg font-bold">Risk: {profile.risks}</p> : null}
      {profile?.usual ? <p className="text-base text-muted">Usual: {profile.usual}</p> : null}

      {flag ? (
        <div>
          <h3 className="text-xl font-bold">{flag.message}</h3>
          <p className="mt-1 text-sm text-muted">A rules engine counted this. Not a diagnosis.</p>
        </div>
      ) : (
        <p className="text-base text-muted">Nothing repeating yet. Speak if something happens tonight.</p>
      )}

      <WeekChart chart={chart} focus={flag?.subtype} />

      {quotes.length ? (
        <div>
          <h3 className="text-lg font-bold">What was said</h3>
          <ul className="mt-2 divide-y divide-line border-y border-line">
            {quotes.map((event) => (
              <li key={event.id || event.event_time} className="py-3">
                <button
                  type="button"
                  className="w-full text-left"
                  onClick={() => event.raw_transcript && onOpenQuote?.(event)}
                >
                  <p className="text-sm font-bold">
                    {voiceLabel(event)}
                    {event.logger_label ? ` · ${event.logger_label.replace(" (home)", "")}` : ""}
                  </p>
                  <p className="text-sm text-muted">
                    {shortWhen(event.event_time)}
                    {event.subtype ? ` · ${eventLabel(event.type, event.subtype)}` : ""}
                  </p>
                  {eventFacts(event) ? <p className="mt-1 text-sm text-muted">{eventFacts(event)}</p> : null}
                  <p className="mt-1 text-base leading-relaxed">{event.detail || event.raw_transcript}</p>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {showPages ? (
        <Press tone="primary" onClick={onBrief}>
          GP page
        </Press>
      ) : null}

      {logCount ? (
        <div>
          <button type="button" className="text-lg font-bold text-accent underline" onClick={() => setShowLogs((value) => !value)}>
            {showLogs ? "Hide logs" : `All logs (${logCount})`}
          </button>
          {showLogs ? <div className="mt-3"><TimelineScreen events={events} onOpenQuote={onOpenQuote} /></div> : null}
        </div>
      ) : null}
    </section>
  );
}
