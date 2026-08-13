export function BrandBar({ right }) {
  return (
    <header className="shrink-0 bg-accent px-5 py-3 text-paper">
      <div className="flex items-center justify-between gap-3">
        <p className="text-lg font-bold tracking-tight">Second Shift</p>
        {right}
      </div>
    </header>
  );
}
