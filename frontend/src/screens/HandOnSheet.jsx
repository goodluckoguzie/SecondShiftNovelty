import { Press } from "../components/Press.jsx";
import { wingFlagLine } from "../labels.js";

export function HandOnSheet({ people, onOpen, onClose }) {
  const flagged = (people || []).filter((row) => (row.flags || []).length);

  return (
    <div className="speak-overlay" role="dialog" aria-modal="true" aria-label="Hand to the next worker">
      <div className="speak-sheet">
        <h2 className="text-2xl font-bold">Hand to the next worker</h2>
        <p className="mt-2 text-lg text-muted">They will see this on the wing when they open Everyone. This is what was said, counted. Not a diagnosis.</p>

        {flagged.length ? (
          <ul className="mt-4 divide-y divide-line border-y border-line">
            {flagged.map((row) => (
              <li key={row.id}>
                <button type="button" className="w-full py-3 text-left" onClick={() => onOpen(row)}>
                  <p className="text-xl font-bold">{row.name}</p>
                  <p className="mt-1 text-base">{wingFlagLine(row) || row.flags[0].message}</p>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 text-lg">Nothing is still open for the next shift.</p>
        )}

        <div className="mt-6">
          <Press tone="primary" onClick={onClose}>
            Done
          </Press>
        </div>
      </div>
    </div>
  );
}
