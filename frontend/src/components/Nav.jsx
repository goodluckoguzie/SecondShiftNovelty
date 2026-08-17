import { IconMic, IconPeople, IconWing } from "./icons.jsx";

const ITEMS = [
  { id: "Board", label: "Wing", Icon: IconWing },
  { id: "Talk", label: "Speak", Icon: IconMic },
  { id: "Person", label: "One to one", Icon: IconPeople },
];

export function Nav({ tab, onChange, hiddenTabs = [], speakOpen = false }) {
  const current = speakOpen
    ? "Talk"
    : tab === "Brief"
      ? "Person"
      : tab === "Talk"
        ? "Talk"
        : tab;
  const items = ITEMS.filter((item) => !hiddenTabs.includes(item.id));
  if (items.length < 2) return null;
  return (
    <nav className="shrink-0 border-t border-line bg-paper pb-2 pt-1">
      <div className="grid" style={{ gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))` }}>
        {items.map(({ id, label, Icon }) => {
          const active = current === id;
          return (
            <button
              key={id}
              type="button"
              aria-current={active ? "page" : undefined}
              className={`flex min-h-[56px] flex-col items-center justify-center gap-0.5 text-base ${
                active ? "font-bold text-accent underline" : "text-muted"
              }`}
              onClick={() => onChange(id)}
            >
              <Icon />
              {label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
