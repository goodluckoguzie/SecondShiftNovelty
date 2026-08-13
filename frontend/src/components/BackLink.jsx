export function BackLink({ onBack, children = "Back" }) {
  return (
    <button type="button" className="mb-4 text-base font-bold text-accent underline" onClick={onBack}>
      {children}
    </button>
  );
}
