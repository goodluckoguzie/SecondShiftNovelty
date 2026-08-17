import { useState } from "react";
import { Press } from "../components/Press.jsx";

export function WhoAbout({ people, hint, busy, onChoose, onCancel }) {
  const [personId, setPersonId] = useState("");
  const [error, setError] = useState("");

  function continueOn() {
    const person = (people || []).find((p) => String(p.id) === personId);
    if (!person) {
      setError("Select the person");
      return;
    }
    onChoose(person);
  }

  return (
    <div className="speak-overlay" role="dialog" aria-modal="true" aria-label="Who is this about">
      <div className="speak-sheet">
        <h2 className="text-2xl font-bold">Who is this about?</h2>
        <p className="mt-2 text-lg text-muted">{hint || "Pick the person this note is for."}</p>
        {error ? (
          <p className="nhs-error mt-4" role="alert">
            {error}
          </p>
        ) : null}
        <label className="mt-4 block">
          <span className="mb-2 block text-lg font-bold">Person</span>
          <select
            className={`nhs-select ${error ? "nhs-select-error" : ""}`}
            value={personId}
            disabled={busy}
            onChange={(e) => {
              setPersonId(e.target.value);
              setError("");
            }}
          >
            <option value="">Select a name</option>
            {(people || []).map((person) => (
              <option key={person.id} value={person.id}>
                {person.name}
              </option>
            ))}
          </select>
        </label>
        <div className="mt-6 space-y-3">
          <Press tone="primary" onClick={continueOn} disabled={busy}>
            Continue
          </Press>
          <Press tone="secondary" onClick={onCancel}>
            Cancel
          </Press>
        </div>
      </div>
    </div>
  );
}
