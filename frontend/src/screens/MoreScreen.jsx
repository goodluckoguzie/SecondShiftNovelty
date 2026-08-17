import { PageHeader } from "../components/PageHeader.jsx";

export function MoreScreen({
  personName,
  canWrite,
  canWriteShift,
  onNotes,
  onWatch,
  onPages,
  onSeveral,
  watchCount,
}) {
  const who = personName || "someone";
  const items = [
    { label: `Notes for ${who}`, onClick: onNotes, show: Boolean(personName) },
    {
      label: watchCount ? `Things to watch (${watchCount})` : "Things to watch",
      onClick: onWatch,
      show: Boolean(personName),
    },
    { label: "Make a page", onClick: onPages, show: Boolean(personName) },
    { label: "Speak about several people", onClick: onSeveral, show: canWrite && canWriteShift },
  ].filter((item) => item.show);

  return (
    <section className="space-y-5">
      <PageHeader title="More" hint={personName ? `For ${personName}.` : "Pick a person first, from People."} />
      {items.length ? (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.label}>
              <button type="button" className="tap-card w-full text-left text-xl font-bold" onClick={item.onClick}>
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-lg text-muted">Open People and tap a name first.</p>
      )}
    </section>
  );
}
