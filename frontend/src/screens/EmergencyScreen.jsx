export function EmergencyScreen({ message, onBack }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-soft px-5 py-10">
      <div className="w-full max-w-md overflow-hidden rounded-md">
        <div className="bg-danger px-5 py-4 text-paper">
          <p className="text-sm font-bold uppercase tracking-wide">Emergency</p>
          <h1 className="mt-1 text-4xl font-bold">Call 999 now</h1>
        </div>
        <div className="bg-paper px-5 py-5">
          <p className="text-lg leading-relaxed">{message}</p>
          <p className="mt-3 text-base leading-relaxed text-muted">
            Second Shift does not use AI for this. If it is not an emergency, call NHS 111.
          </p>
          <button type="button" className="nhs-btn nhs-btn-secondary mt-6" onClick={onBack}>
            Back to the log
          </button>
        </div>
      </div>
    </div>
  );
}
