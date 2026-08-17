import { useState } from "react";
import { BrandBar } from "../components/BrandBar.jsx";
import { Press } from "../components/Press.jsx";

export function PersonPick({ people, whoLabel, onBack, onChoose, busy }) {
  const [personId, setPersonId] = useState("");
  const [error, setError] = useState("");

  function continueOn() {
    const person = people.find((p) => String(p.id) === personId);
    if (!person) {
      setError("Select the person you are with");
      return;
    }
    onChoose(person);
  }

  return (
    <div className="mx-auto flex h-screen max-w-md flex-col bg-soft">
      <BrandBar />
      <main className="flex-1 overflow-auto px-5 py-6">
        <button type="button" className="text-base font-bold text-accent underline" onClick={onBack}>
          Back
        </button>
        <p className="mt-4 text-sm text-muted">{whoLabel}</p>
        <h1 className="mt-1 text-[2rem] font-bold leading-tight">Who are you with?</h1>

        {error && (
          <p className="nhs-error mt-5" role="alert">
            {error}
          </p>
        )}

        <label className="mt-6 block">
          <span className="sr-only">Person</span>
          <select
            className={`nhs-select ${error ? "nhs-select-error" : ""}`}
            value={personId}
            disabled={busy}
            onChange={(e) => {
              setPersonId(e.target.value);
              setError("");
            }}
          >
            <option value="">{people.length ? "Select a person" : "Loading…"}</option>
            {people.map((person) => (
              <option key={person.id} value={person.id}>
                {person.name}
                {person.age ? `, ${person.age}` : ""}
              </option>
            ))}
          </select>
        </label>

        <div className="mt-8">
          <Press tone="primary" onClick={continueOn} disabled={busy}>
            {busy ? "Opening…" : "Continue"}
          </Press>
        </div>
      </main>
    </div>
  );
}
