export function PageHeader({ title, hint }) {
  return (
    <header className="space-y-1">
      <h2 className="text-[1.75rem] font-bold leading-tight">{title}</h2>
      {hint && <p className="text-base leading-relaxed text-muted">{hint}</p>}
    </header>
  );
}
