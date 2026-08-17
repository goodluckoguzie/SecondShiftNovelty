import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BackLink } from "../components/BackLink.jsx";
import { flagTitle, shortWhen } from "../labels.js";
import { theme } from "../theme.js";

function WatchItem({ flag, onOpenQuote }) {
  const [open, setOpen] = useState(false);
  const why = flag.evidence || [];

  return (
    <article className="border-t border-line py-4">
      <h3 className="text-xl font-bold">{flagTitle(flag.subtype)}</h3>
      <p className="mt-1 leading-relaxed">{flag.message}</p>
      {why.length > 0 && (
        <>
          <button
            type="button"
            className="mt-2 font-bold text-accent underline"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? "Hide why" : "Why"}
          </button>
          {open && (
            <ul className="mt-2 space-y-1">
              {why.slice(0, 3).map((event) => (
                <li key={event.id}>
                  <button
                    type="button"
                    className="text-left text-accent underline"
                    onClick={() => onOpenQuote(event)}
                  >
                    {shortWhen(event.event_time)}
                  </button>
                </li>
              ))}
              {why.length > 3 && (
                <li className="text-sm text-muted">and {why.length - 3} more in History</li>
              )}
            </ul>
          )}
        </>
      )}
    </article>
  );
}

export function WeekChart({ chart, focus }) {
  const hasChart = Boolean(chart?.days?.length);
  if (!hasChart) return null;
  const showConfusion = focus !== "vomiting" && focus !== "appetite_low";
  const showVomiting = focus !== "confusion" && focus !== "not_himself" && focus !== "medication";
  const title =
    focus === "vomiting"
      ? "Vomiting logs this week"
      : focus === "confusion"
        ? "Confusion logs this week"
        : "Confusion and vomiting this week";
  const doseDay = chart.dose_change
    ? new Date(chart.dose_change).toLocaleDateString("en-GB", { weekday: "short" })
    : null;

  return (
    <div>
      <h3 className="text-xl font-bold">{title}</h3>
      <p className="mt-1 text-sm text-muted">Count of logs. A rules engine, not a diagnosis.</p>
      <div className="mt-3 h-52">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart.days}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.color.line} />
            <XAxis dataKey="label" tick={{ fontSize: 12, fill: theme.color.ink }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: theme.color.ink }} width={28} />
            <Tooltip />
            {showConfusion && showVomiting ? <Legend /> : null}
            {showConfusion ? <Bar dataKey="confusion" name="Confusion" fill={theme.color.darkBlue} /> : null}
            {showVomiting ? <Bar dataKey="vomiting" name="Vomiting" fill={theme.color.accent} /> : null}
            {doseDay ? (
              <ReferenceLine
                x={doseDay}
                stroke={theme.color.muted}
                label={{ value: "dose change", fill: theme.color.muted, fontSize: 12 }}
              />
            ) : null}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function PatternsScreen({ personName, chart, flags, onOpenQuote, onBack, backLabel }) {
  const openFlags = flags || [];

  return (
    <section>
      {onBack && <BackLink onBack={onBack}>{backLabel}</BackLink>}
      <h2 className="text-[1.75rem] font-bold leading-tight">Watch</h2>
      <p className="mt-1 text-base leading-relaxed text-muted">
        {openFlags.length
          ? `What is still open for ${personName || "them"}.`
          : `Nothing open for ${personName || "this person"}.`}
      </p>

      {openFlags.length > 0 && (
        <div className="mt-4 border-b border-line">
          {openFlags.map((flag) => (
            <WatchItem key={flag.id || flag.message} flag={flag} onOpenQuote={onOpenQuote} />
          ))}
        </div>
      )}

      <div className="mt-8">
        <WeekChart chart={chart} />
      </div>
    </section>
  );
}
