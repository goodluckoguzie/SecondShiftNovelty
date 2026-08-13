import { useState } from "react";
import { PageHeader } from "../components/PageHeader.jsx";
import { Press } from "../components/Press.jsx";
import { eventLabel, shortWhen } from "../labels.js";

export function TalkScreen({
  canWrite,
  transcript,
  setTranscript,
  recording,
  busy,
  confirmation,
  similar,
  flags,
  urgent,
  setUrgent,
  onStart,
  onStop,
  onLog,
  onOpenQuote,
  onOpenWatch,
}) {
  const [typing, setTyping] = useState(false);

  if (!canWrite) {
    return (
      <section className="space-y-2">
        <PageHeader title="Log" hint="Open History to read what happened." />
      </section>
    );
  }

  const watchCount = flags?.length || 0;

  return (
    <section className="space-y-5">
      <PageHeader title="What happened?" />

      {watchCount > 0 && (
        <button type="button" className="text-left font-bold text-accent underline" onClick={onOpenWatch}>
          {watchCount} {watchCount === 1 ? "thing" : "things"} to watch
        </button>
      )}

      {!typing ? (
        <>
          <Press tone={recording ? "warning" : "primary"} onClick={recording ? onStop : onStart} disabled={busy}>
            {recording ? "Stop recording" : "Start speaking"}
          </Press>
          <p className="-mt-2 text-sm text-muted">
            {recording ? "Listening now. Stops after 15 seconds." : busy ? "Saving the log…" : "Say what happened, then press Stop."}
          </p>
          <button type="button" className="font-bold text-accent underline" onClick={() => setTyping(true)}>
            Or type instead
          </button>
        </>
      ) : (
        <>
          <textarea
            aria-label="What happened"
            className="min-h-[110px] w-full rounded-md border-2 border-input bg-paper p-3 text-base leading-relaxed"
            placeholder="Gave dad his 8pm meds, 40 minutes late."
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
          />
          <Press tone="primary" onClick={onLog} disabled={!transcript.trim() || busy}>
            Save log
          </Press>
          <button type="button" className="font-bold text-accent underline" onClick={() => setTyping(false)}>
            Or speak instead
          </button>
        </>
      )}

      <label className="flex items-start gap-3 text-base leading-relaxed">
        <input
          type="checkbox"
          className="mt-1 h-5 w-5 accent-success"
          checked={urgent}
          onChange={(e) => setUrgent(e.target.checked)}
        />
        Put this on the GP page as urgent
      </label>

      {confirmation && <p className="nhs-success text-base leading-relaxed">{confirmation}</p>}

      {similar?.length > 0 && (
        <div className="nhs-inset">
          <p className="font-bold">This has come up before</p>
          <p className="mt-1 text-sm text-muted">Last 14 days. Not a diagnosis.</p>
          <ul className="mt-3 space-y-2">
            {similar.map((event) => (
              <li key={event.id}>
                <button type="button" className="text-left" onClick={() => onOpenQuote(event)}>
                  <span className="font-bold text-accent underline">{eventLabel(event.type, event.subtype)}</span>
                  <span className="ml-2 text-muted">{shortWhen(event.event_time)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
