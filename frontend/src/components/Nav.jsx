import { IconFile, IconFlag, IconList, IconMic } from "./icons.jsx";

const ITEMS = [
  { id: "Talk", label: "Log", Icon: IconMic },
  { id: "Timeline", label: "History", Icon: IconList },
  { id: "Patterns", label: "Watch", Icon: IconFlag },
  { id: "Brief", label: "Pages", Icon: IconFile },
];

export function Nav({ tab, onChange, hiddenTabs = [] }) {
  const items = ITEMS.filter((item) => !hiddenTabs.includes(item.id));
  return (
    <nav className="shrink-0 border-t border-line bg-paper pb-2 pt-1">
      <div className="grid" style={{ gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))` }}>
        {items.map(({ id, label, Icon }) => {
          const active = tab === id;
          return (
            <button
              key={id}
              type="button"
              aria-current={active ? "page" : undefined}
              className={`flex min-h-press flex-col items-center justify-center gap-0.5 text-sm ${
                active ? "font-bold text-accent" : "text-muted"
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
