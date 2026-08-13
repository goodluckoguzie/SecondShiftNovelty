import { useEffect, useState } from "react";
import { pdfUrl } from "../api.js";
import { BriefPage } from "../components/BriefPage.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { Press } from "../components/Press.jsx";

export function BriefScreen({
  busy,
  briefMd,
  handoverMd,
  hasBrief,
  hasHandover,
  onBrief,
  onHandoverShift,
  onHandoverFamily,
  canWriteShift,
}) {
  const [kind, setKind] = useState("gp");
  const [windowKind, setWindowKind] = useState(canWriteShift ? "shift" : "family");
  const [showForm, setShowForm] = useState(true);

  const preview = kind === "gp" ? briefMd : handoverMd;
  const hasPdf = kind === "gp" ? hasBrief : hasHandover;

  useEffect(() => {
    setShowForm(!preview);
  }, [preview, kind]);

  function makePage() {
    if (kind === "gp") onBrief();
    else if (windowKind === "shift") onHandoverShift();
    else onHandoverFamily();
  }

  const title = preview ? (kind === "gp" ? "GP page" : "Handover") : "Pages";

  return (
    <section className="space-y-5">
      <PageHeader title={title} hint={preview ? undefined : "A page the next person can take."} />

      {preview && <BriefPage markdown={preview} />}

      {hasPdf && (
        <a
          className="nhs-btn nhs-btn-secondary block text-center"
          href={pdfUrl(kind === "gp" ? "gp" : "handover")}
          target="_blank"
          rel="noreferrer"
        >
          Open PDF
        </a>
      )}

      {preview && !showForm && (
        <button type="button" className="font-bold text-accent underline" onClick={() => setShowForm(true)}>
          Make another
        </button>
      )}

      {showForm && (
        <>
          <fieldset>
            <legend className="text-lg font-bold">What do you need?</legend>
            <label className="nhs-radio">
              <input type="radio" name="kind" value="gp" checked={kind === "gp"} onChange={() => setKind("gp")} />
              <span>
                <span className="block text-lg font-bold">GP page</span>
                <span className="block text-base text-muted">One page they can take</span>
              </span>
            </label>
            <label className="nhs-radio">
              <input
                type="radio"
                name="kind"
                value="handover"
                checked={kind === "handover"}
                onChange={() => setKind("handover")}
              />
              <span>
                <span className="block text-lg font-bold">Handover</span>
                <span className="block text-base text-muted">For the next person</span>
              </span>
            </label>
          </fieldset>

          {kind === "handover" && (
            <fieldset>
              <legend className="text-lg font-bold">Which window?</legend>
              {canWriteShift && (
                <label className="nhs-radio">
                  <input
                    type="radio"
                    name="window"
                    value="shift"
                    checked={windowKind === "shift"}
                    onChange={() => setWindowKind("shift")}
                  />
                  <span className="text-lg">This shift</span>
                </label>
              )}
              <label className="nhs-radio">
                <input
                  type="radio"
                  name="window"
                  value="family"
                  checked={windowKind === "family"}
                  onChange={() => setWindowKind("family")}
                />
                <span className="text-lg">Family, 72 hours</span>
              </label>
            </fieldset>
          )}

          <Press tone="primary" onClick={makePage} disabled={busy}>
            Make page
          </Press>
        </>
      )}
    </section>
  );
}
