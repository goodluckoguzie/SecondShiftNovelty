export function CardLink({ title, hint, onClick, disabled, leading }) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="nhs-card flex w-full items-center gap-3 px-4 py-4 text-left"
    >
      {leading}
      <span className="min-w-0 flex-1">
        <span className="block text-xl font-bold text-accent">{title}</span>
        {hint && <span className="mt-1 block text-base text-muted">{hint}</span>}
      </span>
      <span aria-hidden className="text-2xl font-bold text-accent">
        ›
      </span>
    </button>
  );
}
