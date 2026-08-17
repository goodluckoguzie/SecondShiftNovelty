import { wingFlagLine } from "../labels.js";

export function BoardScreen({ board, canWrite, onOpenPerson, onHandOn }) {
  const people = board?.people || [];
  const flagged = people.filter((row) => (row.flags || []).length);
  const rest = people.filter((row) => !(row.flags || []).length);

  return (
    <section className="space-y-5">
      <h2 className="text-[1.75rem] font-bold leading-tight">Everyone</h2>
      <p className="text-base leading-relaxed text-muted">
        {canWrite ? "Tap a name to read. Speak to write." : "Tap a name to read."}
      </p>

      {canWrite && onHandOn ? (
        <button type="button" className="text-lg font-bold text-accent underline" onClick={onHandOn}>
          Hand to the next worker
        </button>
      ) : null}

      {flagged.length ? (
        <div>
          <h3 className="mb-2 text-lg font-bold">Still open for the next shift</h3>
          <NameList people={flagged} onOpenPerson={onOpenPerson} showFlag />
        </div>
      ) : null}

      <NameList
        title={flagged.length ? "Everyone else" : null}
        people={rest}
        onOpenPerson={onOpenPerson}
      />

      {!people.length ? <p className="text-lg text-muted">No one is on this wing yet.</p> : null}
    </section>
  );
}

function NameList({ title, people, onOpenPerson, showFlag }) {
  if (!people.length) return null;
  return (
    <div>
      {title ? <h3 className="mb-2 text-lg font-bold">{title}</h3> : null}
      <ul className="space-y-3">
        {people.map((row) => (
          <li key={row.id}>
            <button type="button" className="tap-card w-full py-5 text-left" onClick={() => onOpenPerson(row)}>
              <span className="block text-2xl font-bold">{row.name}</span>
              {showFlag && wingFlagLine(row) ? (
                <span className="mt-1 block text-base leading-relaxed">{wingFlagLine(row)}</span>
              ) : null}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
