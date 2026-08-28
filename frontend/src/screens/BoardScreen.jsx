import { personPhoto } from "../people.js";
import { wingCardLine, wingCarryLine } from "../labels.js";

export function BoardScreen({ board, canWrite, onOpenPerson, onHandOn }) {
  const people = board?.people || [];
  const openCount = people.filter((row) => (row.flags || []).length).length;
  const openLabel = openCount ? `${openCount} still open` : "Nothing still open";

  return (
    <section className="flex min-h-full flex-1 flex-col gap-3">
      <div className="flex shrink-0 items-baseline justify-between gap-3">
        <p className="text-[13px] text-muted">{openLabel}</p>
        {canWrite && onHandOn ? (
          <button type="button" className="text-[13px] font-semibold text-accent" onClick={onHandOn}>
            Handover
          </button>
        ) : null}
      </div>

      {people.length ? (
        <ul className="grid min-h-0 flex-1 grid-cols-2 gap-2 [grid-auto-rows:minmax(4.75rem,1fr)]">
          {people.map((row) => (
            <li key={row.id} className="min-h-0">
              <PersonCard row={row} onClick={() => onOpenPerson(row)} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-base text-muted">No one is on this wing yet.</p>
      )}
    </section>
  );
}

function PersonCard({ row, onClick }) {
  const photo = personPhoto(row.name);
  const carry = wingCarryLine(row);
  const line = wingCardLine(row);
  const initial = (row.name || "?").trim().charAt(0);

  return (
    <button
      type="button"
      className="relative flex h-full min-h-[4.75rem] w-full items-center gap-2 overflow-hidden rounded-xl border border-line bg-paper p-1.5 text-left"
      onClick={onClick}
      aria-label={`${row.name}, ${line}`}
    >
      {photo ? (
        <img src={photo} alt="" className="h-full w-[4.5rem] shrink-0 self-stretch rounded-lg object-cover" />
      ) : (
        <span className="flex h-full w-[4.5rem] shrink-0 items-center justify-center self-stretch rounded-lg bg-dark-blue text-2xl font-bold text-paper">
          {initial}
        </span>
      )}
      <span className="flex min-w-0 flex-1 flex-col justify-center py-1 pr-5">
        <span className="block truncate text-[15px] font-bold leading-tight">{row.name}</span>
        <span className={`mt-0.5 line-clamp-2 text-[12px] leading-snug ${carry ? "font-semibold text-ink" : "text-muted"}`}>
          {line}
        </span>
      </span>
      {carry ? (
        <svg
          className="absolute right-1.5 top-1.5 text-danger"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden
        >
          <path d="M6 3v18h2V14h8.5l-1.2-3.5L16.5 7H8V3H6z" />
        </svg>
      ) : null}
    </button>
  );
}
