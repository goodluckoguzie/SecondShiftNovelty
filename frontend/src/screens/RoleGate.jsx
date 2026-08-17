import { useState } from "react";
import { BrandBar } from "../components/BrandBar.jsx";
import { Press } from "../components/Press.jsx";

export function RoleGate({
  workers,
  people = [],
  onChooseWorker,
  onChooseFamily,
  onChooseClinical,
  onChooseAdmin,
  gateError,
}) {
  const [path, setPath] = useState("");
  const [workerId, setWorkerId] = useState("");
  const [personId, setPersonId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function goShift() {
    const worker = workers.find((w) => String(w.id) === workerId);
    if (!worker) {
      setError("Select your name");
      return;
    }
    if (!password.trim()) {
      setError("Type the password");
      return;
    }
    onChooseWorker(worker, password);
  }

  function goFamily() {
    const person = (people || []).find((p) => String(p.id) === personId);
    if (!person) {
      setError("Select the person");
      return;
    }
    if (!password.trim()) {
      setError("Type the password");
      return;
    }
    onChooseFamily(person, password);
  }

  function goAdmin() {
    if (!password.trim()) {
      setError("Type the password");
      return;
    }
    onChooseAdmin(password);
  }

  return (
    <div className="mx-auto flex h-screen max-w-md flex-col bg-soft">
      <BrandBar />
      <main className="flex-1 overflow-auto px-5 py-6">
        <h1 className="text-[2rem] font-bold leading-tight">Who are you?</h1>

        {(error || gateError) && (
          <p className="nhs-error mt-5" role="alert">
            {error || gateError}
          </p>
        )}

        {!path ? (
          <div className="mt-6 space-y-3">
            <button type="button" className="tap-card w-full text-left" onClick={() => {
              setPassword("");
              setWorkerId("");
              setError("");
              setPath("shift");
            }}>
              <span className="block text-xl font-bold">Support worker</span>
              <span className="mt-1 block text-base text-muted">I work here. Pick your name next</span>
            </button>
            <button
              type="button"
              className="tap-card w-full text-left"
              onClick={() => {
                setPassword("");
                setPersonId("");
                setError("");
                if (!(people || []).length) {
                  setError("No one is on this wing yet");
                  return;
                }
                setPath("family");
              }}
            >
              <span className="block text-xl font-bold">Family</span>
              <span className="mt-1 block text-base text-muted">A note from home. Pick who it is about</span>
            </button>
            <button type="button" className="tap-card w-full text-left" onClick={() => onChooseClinical()}>
              <span className="block text-xl font-bold">Nurse or GP</span>
              <span className="mt-1 block text-base text-muted">Read only</span>
            </button>
            <button
              type="button"
              className="tap-card w-full text-left"
              onClick={() => {
                setPassword("");
                setError("");
                setPath("admin");
              }}
            >
              <span className="block text-xl font-bold">Admin</span>
              <span className="mt-1 block text-base text-muted">Add people and staff</span>
            </button>
          </div>
        ) : null}

        {path === "shift" ? (
          <div className="mt-6 space-y-4">
            <button type="button" className="text-lg font-bold text-accent underline" onClick={() => setPath("")}>
              Back
            </button>
            <label className="block">
              <span className="mb-2 block text-xl font-bold">Your name</span>
              <select
                className={`nhs-select ${error === "Select your name" ? "nhs-select-error" : ""}`}
                value={workerId}
                onChange={(e) => {
                  setWorkerId(e.target.value);
                  setError("");
                }}
              >
                <option value="">{workers.length ? "Select your name" : "Loading…"}</option>
                {workers.map((worker) => (
                  <option key={worker.id} value={worker.id}>
                    {worker.display_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-xl font-bold">Password</span>
              <input
                type="password"
                className="nhs-select"
                value={password}
                autoComplete="off"
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError("");
                }}
              />
            </label>
            <Press tone="primary" onClick={goShift}>
              Continue
            </Press>
          </div>
        ) : null}

        {path === "family" ? (
          <div className="mt-6 space-y-4">
            <button type="button" className="text-lg font-bold text-accent underline" onClick={() => setPath("")}>
              Back
            </button>
            <label className="block">
              <span className="mb-2 block text-xl font-bold">Who is this about?</span>
              <select
                className={`nhs-select ${error === "Select the person" ? "nhs-select-error" : ""}`}
                value={personId}
                onChange={(e) => {
                  setPersonId(e.target.value);
                  setError("");
                }}
              >
                <option value="">{people.length ? "Select a person" : "Loading…"}</option>
                {people.map((person) => (
                  <option key={person.id} value={person.id}>
                    {person.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-xl font-bold">Password</span>
              <input
                type="password"
                className="nhs-select"
                value={password}
                autoComplete="off"
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError("");
                }}
              />
            </label>
            <Press tone="primary" onClick={goFamily}>
              Continue
            </Press>
          </div>
        ) : null}

        {path === "admin" ? (
          <div className="mt-6 space-y-4">
            <button type="button" className="text-lg font-bold text-accent underline" onClick={() => setPath("")}>
              Back
            </button>
            <label className="block">
              <span className="mb-2 block text-xl font-bold">Admin password</span>
              <input
                type="password"
                className="nhs-select"
                value={password}
                autoComplete="off"
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError("");
                }}
              />
            </label>
            <Press tone="primary" onClick={goAdmin}>
              Continue
            </Press>
          </div>
        ) : null}

        <p className="mt-10 text-sm leading-relaxed text-muted">
          Demo only. This organises notes. It does not diagnose, and it is not an NHS service.
        </p>
      </main>
    </div>
  );
}
