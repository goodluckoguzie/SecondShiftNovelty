import { PageHeader } from "../components/PageHeader.jsx";
import { Press } from "../components/Press.jsx";

export function CorridorScreen({ recording, busy, status, confirmation, onStart, onStop, onBack }) {
  return (
    <section className="space-y-5">
      <button type="button" className="text-lg font-bold text-accent underline" onClick={onBack}>
        Back
      </button>
      <PageHeader title="Several people" hint="Say the name, then what happened. Then the next name." />
      <Press tone={recording ? "warning" : "primary"} onClick={recording ? onStop : onStart} disabled={busy}>
        {recording ? "Stop" : "Speak"}
      </Press>
      <p className="-mt-2 text-center text-lg text-muted">
        {recording ? "Listening…" : status === "writing" || status === "saving" ? "Saving…" : "Press Speak."}
      </p>
      {confirmation ? <p className="nhs-success text-lg font-bold">{confirmation}</p> : null}
    </section>
  );
}
