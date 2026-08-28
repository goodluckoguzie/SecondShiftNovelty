import { useState } from "react";
import { Press } from "../components/Press.jsx";

export function SpeakOverlay({
  recording,
  busy,
  status,
  aboutName,
  whoName,
  error,
  transcript,
  setTranscript,
  onStop,
  onCancel,
  onDiscardMic,
  onSaveTyped,
  onRetry,
}) {
  const [typing, setTyping] = useState(false);
  const saving = status === "saving" || (busy && !recording && status !== "writing" && status !== "check");
  const hearing = status === "writing";
  const checking = status === "check" || typing;
  const locked = Boolean(aboutName);
  const writer = (whoName || "Staff").split(" ")[0];

  return (
    <div className="speak-overlay" role="dialog" aria-modal="true" aria-label="Recording">
      <div className="speak-sheet">
        <p className="text-xl font-bold">
          {saving ? "Saving" : hearing ? "Hearing you" : checking ? "What you said" : "Recording"}
        </p>
        <p className="mt-2 text-lg text-muted">
          {saving
            ? "Writing it down…"
            : hearing
              ? `${writer} is writing what you said.`
              : checking
                ? locked
                  ? `This note is for ${aboutName}. Check it, then Save.`
                  : "Check it, then Save."
                : "Stay here until Stop"}
        </p>

        {!checking && !saving && !hearing ? (
          <div className="speak-wave" aria-hidden>
            {Array.from({ length: 24 }, (_, i) => (
              <span key={i} style={{ animationDelay: `${(i % 8) * 0.08}s` }} />
            ))}
          </div>
        ) : null}

        {error ? (
          <p className="nhs-error mt-4 text-base" role="alert">
            {error}
          </p>
        ) : null}

        {checking ? (
          <>
            <textarea
              aria-label="What you said"
              className="mt-4 min-h-[120px] w-full rounded-lg border-2 border-input bg-paper p-3 text-lg leading-relaxed"
              placeholder={locked ? "He barely touched supper." : "Able up at two. Frank was tearful."}
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
            />
            <div className="mt-4 space-y-3">
              <Press tone="primary" onClick={onSaveTyped} disabled={!transcript.trim() || busy}>
                Save
              </Press>
              {onRetry ? (
                <Press
                  tone="secondary"
                  onClick={() => {
                    setTyping(false);
                    onRetry();
                  }}
                >
                  Speak again
                </Press>
              ) : null}
              <Press tone="secondary" onClick={onCancel}>
                Cancel
              </Press>
            </div>
          </>
        ) : saving || hearing ? (
          <p className="mt-4 text-lg font-bold">{hearing ? "Keep this screen open." : "Keep this screen open."}</p>
        ) : (
          <>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <Press tone="secondary" onClick={onCancel}>
                Cancel
              </Press>
              <Press tone="warning" onClick={onStop} disabled={busy}>
                Stop
              </Press>
            </div>
            <button
              type="button"
              className="mt-4 w-full text-lg font-bold text-accent underline"
              onClick={() => {
                onDiscardMic();
                setTyping(true);
              }}
            >
              Type instead
            </button>
          </>
        )}
      </div>
    </div>
  );
}
