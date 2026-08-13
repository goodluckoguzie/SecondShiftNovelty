import { useState } from "react";
import { BrandBar } from "../components/BrandBar.jsx";
import { Press } from "../components/Press.jsx";

export function RoleGate({ workers, onChooseWorker, onChooseClinical }) {
  const [path, setPath] = useState("");
  const [workerId, setWorkerId] = useState("");
  const [error, setError] = useState("");

  function continueOn() {
    if (!path) {
      setError("Select how you are using this");
      return;
    }
    if (path === "clinical") {
      setError("");
      onChooseClinical();
      return;
    }
    const worker = workers.find((w) => String(w.id) === workerId);
    if (!worker) {
      setError("Select your name");
      return;
    }
    setError("");
    onChooseWorker(worker);
  }

  return (
    <div className="mx-auto flex h-screen max-w-md flex-col bg-soft">
      <BrandBar />
      <main className="flex-1 overflow-auto px-5 py-6">
        <h1 className="text-[2rem] font-bold leading-tight">Who is here?</h1>

        {error && (
          <p className="nhs-error mt-5" role="alert">
            {error}
          </p>
        )}

        <fieldset className="mt-6">
          <legend className="text-lg font-bold">How are you using this?</legend>
          <label className="nhs-radio">
            <input
              type="radio"
              name="path"
              value="shift"
              checked={path === "shift"}
              onChange={() => {
                setPath("shift");
                setError("");
              }}
            />
            <span>
              <span className="block text-lg font-bold">I am on shift</span>
              <span className="block text-base text-muted">Speak or type a log</span>
            </span>
          </label>
          <label className="nhs-radio">
            <input
              type="radio"
              name="path"
              value="clinical"
              checked={path === "clinical"}
              onChange={() => {
                setPath("clinical");
                setWorkerId("");
                setError("");
              }}
            />
            <span>
              <span className="block text-lg font-bold">Nurse or GP</span>
              <span className="block text-base text-muted">Read only. Same record</span>
            </span>
          </label>
        </fieldset>

        {path === "shift" && (
          <label className="mt-6 block">
            <span className="mb-2 block text-lg font-bold">Your name</span>
            <select
              className={`nhs-select ${error === "Select your name" ? "nhs-select-error" : ""}`}
              value={workerId}
              onChange={(e) => {
                setWorkerId(e.target.value);
                setError("");
              }}
            >
              <option value="">{workers.length ? "Select your name" : "Loading names…"}</option>
              {workers.map((worker) => (
                <option key={worker.id} value={worker.id}>
                  {worker.display_name}
                </option>
              ))}
            </select>
          </label>
        )}

        <div className="mt-8">
          <Press tone="primary" onClick={continueOn}>
            Continue
          </Press>
        </div>

        <p className="mt-8 text-sm leading-relaxed text-muted">
          Demo only. This organises notes. It does not diagnose, and it is not an NHS service.
        </p>
      </main>
    </div>
  );
}
