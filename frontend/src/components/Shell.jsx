import { useState } from "react";
import { BrandBar } from "./BrandBar.jsx";
import { Nav } from "./Nav.jsx";

export function Shell({
  profile,
  people,
  whoLabel,
  tab,
  onTab,
  hiddenTabs,
  children,
  onPickPerson,
  onSwitchWho,
  viewOnly,
}) {
  const [changing, setChanging] = useState(false);
  const firstName = whoLabel.split(" ")[0];

  return (
    <div className="mx-auto flex h-screen max-w-md flex-col bg-soft">
      <BrandBar
        right={
          <button type="button" className="text-sm font-bold underline" onClick={onSwitchWho}>
            Not {firstName}?
          </button>
        }
      />

      <div className="shrink-0 border-b border-line bg-paper px-5 py-3">
        <div className="flex items-baseline justify-between gap-3">
          <p className="text-lg font-bold leading-tight">
            {profile?.name || "…"}
            {profile?.age ? <span className="ml-2 text-base font-normal text-muted">{profile.age}</span> : null}
            {viewOnly ? <span className="ml-2 text-sm font-normal text-muted">Read only</span> : null}
          </p>
          <button
            type="button"
            className="shrink-0 text-sm font-bold text-accent underline"
            onClick={() => setChanging((value) => !value)}
          >
            {changing ? "Cancel" : "Change"}
          </button>
        </div>
        {changing && (
          <select
            className="nhs-select mt-2"
            value={profile?.id || ""}
            onChange={(e) => {
              onPickPerson(Number(e.target.value));
              setChanging(false);
            }}
          >
            {(people || []).map((person) => (
              <option key={person.id} value={person.id}>
                {person.name}
                {person.age ? ` · ${person.age}` : ""}
              </option>
            ))}
          </select>
        )}
      </div>

      <main className="flex-1 space-y-4 overflow-auto px-5 py-5">{children}</main>
      <Nav tab={tab} onChange={onTab} hiddenTabs={hiddenTabs} />
    </div>
  );
}
