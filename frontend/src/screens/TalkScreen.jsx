import { useEffect, useState } from "react";
import { PageHeader } from "../components/PageHeader.jsx";
import { Press } from "../components/Press.jsx";
import { eventLabel, joinCopy, shortWhen } from "../labels.js";

export function TalkScreen({
  canWrite,
  aboutId,
  onAboutChange,
  people,
  personName,
  assignedPersonId,
  transcript,
  setTranscript,
  recording,
  busy,
  status,
  confirmation,
  warning,
  slices,
  events,
  onStart,
  onStop,
  onLog,
  onOpenQuote,
  onOpenSlice,
  lockPerson,
}) {
  const [typing, setTyping] = useState(false);
  const aboutWing = aboutId === "wing" || aboutId == null;
  const notes = aboutWing ? [] : (events || []).slice(0, 12);
  const ordered = [...(people || [])].sort((a, b) => {
    if (a.id === assignedPersonId) return -1;
    if (b.id === assignedPersonId) return 1;
    return (a.name || "").localeCompare(b.name || "");
  });

  useEffect(() => {
    if (confirmation) setTyping(false);
  }, [confirmation]);

  return (
    <section className="space-y-5">
      <PageHeader
        title="Speak"
        hint={
          aboutWing
            ? "Say the name, then what happened. You can name more than one person."
            : `This note is for ${personName || "them"} only.`
        }
      />

      {lockPerson ? <p className="tap-card text-lg font-bold">{personName}</p> : null}

      {canWrite ? (
        !typing ? (
          <>
            <Press tone={recording ? "warning" : "primary"} onClick={recording ? onStop : onStart} disabled={busy}>
              {recording ? "Stop" : "Speak"}
            </Press>
            <p className="-mt-2 text-center text-lg text-muted">
              {recording
                ? aboutWing
                  ? "Listening. Name the person, then the line."
                  : "Listening…"
                : status === "writing" || status === "saving"
                  ? "Saving…"
                  : aboutWing
                    ? "Example: Able up at two. Frank was tearful."
                    : "Press Speak. Talk. Press Stop."}
            </p>
            {transcript.trim() ? (
              <div className="tap-card">
                <p className="font-bold">You said</p>
                <p className="mt-2 text-lg leading-relaxed">“{transcript.trim()}”</p>
              </div>
            ) : null}
            {confirmation ? <p className="nhs-success text-lg font-bold">{confirmation}</p> : null}
            {warning ? <p className="nhs-error text-base">{warning}</p> : null}
            {slices?.length ? (
              <ul className="overflow-hidden rounded-xl border-2 border-line bg-paper">
                {slices.map((slice) => (
                  <li key={slice.person_id || slice.person_name} className="border-b border-line last:border-b-0">
                    <button
                      type="button"
                      className="w-full px-4 py-3 text-left"
                      onClick={() => onOpenSlice?.(slice)}
                      disabled={!slice.person_id}
                    >
                      <p className="font-bold">{slice.person_name}</p>
                      <p className="text-base">{slice.transcript}</p>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </>
        ) : (
          <>
            <textarea
              aria-label="What happened"
              className="min-h-[120px] w-full rounded-lg border-2 border-input bg-paper p-3 text-lg leading-relaxed"
              placeholder={aboutWing ? "Able up at two. Frank was tearful." : "He barely touched supper."}
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
            />
            <Press tone="primary" onClick={onLog} disabled={!transcript.trim() || busy}>
              Save
            </Press>
            {confirmation ? <p className="nhs-success text-lg font-bold">{confirmation}</p> : null}
            {warning ? <p className="nhs-error text-base">{warning}</p> : null}
          </>
        )
      ) : (
        <p className="text-lg text-muted">Read only. Open a name on the wing to see notes.</p>
      )}

      {!lockPerson ? (
        <div>
          <p className="mb-2 text-lg font-bold">Who is this about?</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={`about-chip ${aboutWing ? "about-chip-on" : ""}`}
              onClick={() => onAboutChange("wing")}
            >
              Say the name
            </button>
            {ordered.map((person) => (
              <button
                key={person.id}
                type="button"
                className={`about-chip ${!aboutWing && Number(aboutId) === person.id ? "about-chip-on" : ""}`}
                onClick={() => onAboutChange(person.id)}
              >
                {person.name}
              </button>
            ))}
          </div>
          <p className="mt-2 text-base text-muted">
            Leave this on Say the name, and say who you mean. Tap a name only if you want this note locked to them.
          </p>
        </div>
      ) : null}

      {canWrite ? (
        <button
          type="button"
          className="text-lg font-bold text-accent underline"
          onClick={() => setTyping((value) => !value)}
        >
          {typing ? "Speak instead" : "Type instead"}
        </button>
      ) : null}

      {!aboutWing ? (
        <div className="tap-card">
          <p className="text-xl font-bold">{personName ? `Notes for ${personName}` : "Notes"}</p>
          {notes.length ? (
            <ul className="mt-3 divide-y divide-line">
              {notes.map((event) => (
                <li key={event.id} className="py-3">
                  <button type="button" className="w-full text-left" onClick={() => onOpenQuote(event)}>
                    <p className="text-sm text-muted">
                      {joinCopy(
                        eventLabel(event.type, event.subtype),
                        event.logger_label,
                        event.event_time ? shortWhen(event.event_time) : "",
                      )}
                    </p>
                    <p className="mt-1 text-base leading-relaxed">{event.detail || event.raw_transcript}</p>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-base text-muted">Nothing written yet.</p>
          )}
        </div>
      ) : null}
    </section>
  );
}
