import { BrandBar } from "./BrandBar.jsx";
import { Nav } from "./Nav.jsx";

export function Shell({ whoLabel, tab, onTab, hiddenTabs, children, overlay, onSwitchWho, viewOnly, onBack, speakOpen }) {
  const firstName = whoLabel.split(" ")[0];

  return (
    <div className="mx-auto flex h-screen max-w-md flex-col bg-soft">
      <BrandBar
        right={
          <button type="button" className="text-base font-bold underline" onClick={onSwitchWho}>
            Not {firstName}?
          </button>
        }
      />
      {viewOnly ? <p className="border-b border-line bg-paper px-5 py-2 text-sm font-bold text-muted">Read only</p> : null}
      <main className="relative min-h-0 flex-1">
        <div className="h-full space-y-4 overflow-auto px-5 py-5">
          {onBack ? (
            <button type="button" className="text-lg font-bold text-accent underline" onClick={onBack}>
              Back
            </button>
          ) : null}
          {children}
        </div>
        {overlay}
      </main>
      <Nav tab={tab} onChange={onTab} hiddenTabs={hiddenTabs} speakOpen={speakOpen} />
    </div>
  );
}
