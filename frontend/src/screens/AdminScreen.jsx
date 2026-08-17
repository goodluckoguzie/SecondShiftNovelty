import { useState } from "react";
import { BrandBar } from "../components/BrandBar.jsx";
import { Press } from "../components/Press.jsx";

export function AdminScreen({ people, workers, busy, error, onAddPerson, onAddStaff, onAssign, onLeave }) {
  const [personName, setPersonName] = useState("");
  const [personAge, setPersonAge] = useState("80");
  const [personRisks, setPersonRisks] = useState("");
  const [staffName, setStaffName] = useState("");
  const [staffPerson, setStaffPerson] = useState("");

  return (
    <div className="mx-auto flex h-screen max-w-md flex-col bg-soft">
      <BrandBar
        right={
          <button type="button" className="text-sm font-bold underline" onClick={onLeave}>
            Back
          </button>
        }
      />
      <main className="flex-1 space-y-8 overflow-auto px-5 py-6">
        <h1 className="text-[2rem] font-bold leading-tight">Admin</h1>
        <p className="text-base text-muted">Demo only. This is not NHS login.</p>
        {error ? (
          <p className="nhs-error" role="alert">
            {error}
          </p>
        ) : null}

        <section className="space-y-3">
          <h2 className="text-lg font-bold">People on the wing</h2>
          {people.length ? (
            <ul className="divide-y divide-line border-y border-line bg-paper">
              {people.map((person) => (
                <li key={person.id} className="px-3 py-3">
                  <p className="font-bold">{person.name}</p>
                  <p className="text-sm text-muted">
                    {[person.age, person.risks].filter(Boolean).join(", ") || "No risk noted"}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-base text-muted">None yet.</p>
          )}
        </section>

        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            onAddPerson({
              name: personName,
              age: Number(personAge) || 80,
              risks: personRisks,
            }).then(() => {
              setPersonName("");
              setPersonAge("80");
              setPersonRisks("");
            });
          }}
        >
          <h2 className="text-lg font-bold">Add a person</h2>
          <label className="block">
            <span className="mb-2 block font-bold">Name</span>
            <input className="nhs-select" value={personName} onChange={(e) => setPersonName(e.target.value)} required />
          </label>
          <label className="block">
            <span className="mb-2 block font-bold">Age</span>
            <input className="nhs-select" inputMode="numeric" value={personAge} onChange={(e) => setPersonAge(e.target.value)} />
          </label>
          <label className="block">
            <span className="mb-2 block font-bold">Risk in ten seconds (optional)</span>
            <input
              className="nhs-select"
              placeholder="chokes on thin fluids"
              value={personRisks}
              onChange={(e) => setPersonRisks(e.target.value)}
            />
          </label>
          <Press type="submit" tone="primary" disabled={busy || !personName.trim()}>
            Add person
          </Press>
        </form>

        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            onAddStaff({
              display_name: staffName,
              assigned_person_id: staffPerson ? Number(staffPerson) : null,
            }).then(() => {
              setStaffName("");
              setStaffPerson("");
            });
          }}
        >
          <h2 className="text-lg font-bold">Add a support worker</h2>
          <label className="block">
            <span className="mb-2 block font-bold">Name</span>
            <input className="nhs-select" value={staffName} onChange={(e) => setStaffName(e.target.value)} required />
          </label>
          <label className="block">
            <span className="mb-2 block font-bold">Assigned person (optional)</span>
            <select className="nhs-select" value={staffPerson} onChange={(e) => setStaffPerson(e.target.value)}>
              <option value="">Whole wing, not assigned</option>
              {people.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>
          <Press type="submit" tone="primary" disabled={busy || !staffName.trim()}>
            Add staff
          </Press>
        </form>

        <section className="space-y-3">
          <h2 className="text-lg font-bold">Who is assigned</h2>
          <ul className="divide-y divide-line border-y border-line bg-paper">
            {workers.map((worker) => (
              <li key={worker.id} className="px-3 py-3">
                <p className="font-bold">{worker.display_name}</p>
                <label className="mt-2 block">
                  <span className="sr-only">Assign {worker.display_name}</span>
                  <select
                    className="nhs-select"
                    value={worker.assigned_person_id || ""}
                    onChange={(e) => onAssign(worker.id, e.target.value ? Number(e.target.value) : null)}
                    disabled={busy}
                  >
                    <option value="">Whole wing</option>
                    {people.map((person) => (
                      <option key={person.id} value={person.id}>
                        {person.name}
                      </option>
                    ))}
                  </select>
                </label>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
}
