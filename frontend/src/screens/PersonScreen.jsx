import { useMemo, useState } from "react";
import { postJson } from "../api.js";
import { Avatar } from "../components/Avatar.jsx";
import { clock, eventLabel } from "../labels.js";

const WEEKDAYS = ["M", "T", "W", "T", "F", "S", "S"];
const UNSETTLED = new Set([
  "fall",
  "vomiting",
  "confusion",
  "agitation",
  "dose_late",
  "dose_missed",
  "appetite_low",
  "mood_low",
  "not_himself",
  "awake_night",
]);

function sameDay(iso, date) {
  const at = new Date(iso);
  return at.getFullYear() === date.getFullYear() && at.getMonth() === date.getMonth() && at.getDate() === date.getDate();
}

function dayKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function cardTone(event) {
  const type = event.type || "";
  const subtype = event.subtype || "";
  if (type === "medication" || subtype === "dose_late" || subtype === "dose_missed") {
    return "border-[#d5281b] bg-[#f8d7d4]";
  }
  if (type === "meal" || subtype === "eaten" || subtype === "appetite_low") {
    return "border-[#007f3b] bg-[#cce5d6]";
  }
  if (type === "symptom" || subtype === "vomiting" || subtype === "confusion" || subtype === "agitation") {
    return "border-[#ed8b00] bg-[#fff2cc]";
  }
  if (type === "mood" || subtype === "not_himself" || subtype === "mood_low") {
    return "border-[#005eb8] bg-[#d6e8f6]";
  }
  if (type === "sleep") {
    return "border-[#003087] bg-[#e8eef7]";
  }
  if (type === "incident" || subtype === "fall") {
    return "border-[#d5281b] bg-[#fce4e2]";
  }
  return "border-line bg-paper";
}

function AskNotes({ name, onOpenQuote }) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function ask() {
    const text = question.trim();
    if (!text || busy) return;
    setBusy(true);
    setError("");
    try {
      const payload = await postJson("/person/ask", { question: text });
      setResult(payload);
    } catch (err) {
      setResult(null);
      setError(err.message || "Could not ask the notes.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3">
      <p className="mb-2 text-[13px] text-muted">Ollama reads the stored notes. Counts come from the record.</p>
      <textarea
        className="w-full rounded-lg border-2 border-input bg-paper px-3 py-2 text-[15px] leading-snug"
        rows={3}
        value={question}
        disabled={busy}
        placeholder="Has he eaten today?"
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button
        type="button"
        className="mt-2 text-[13px] font-semibold text-accent"
        disabled={busy || !question.trim()}
        onClick={ask}
      >
        {busy ? "Reading the notes…" : "Ask"}
      </button>
      {error ? (
        <p className="nhs-error mt-2 text-[13px]" role="alert">
          {error}
        </p>
      ) : null}
      {result ? (
        <div className="mt-3 rounded-lg bg-soft px-3 py-2">
          <p className="text-[15px] leading-relaxed">{result.answer}</p>
          <p className="mt-2 text-[12px] text-muted">{result.disclaimer || "From the stored notes. Not a diagnosis."}</p>
          {result.cites?.length ? (
            <ul className="mt-3 space-y-2">
              {result.cites.map((event) => (
                <li key={event.id}>
                  <LogCard event={event} onOpenQuote={onOpenQuote} />
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function LogCard({ event, onOpenQuote }) {
  const who = (event.logger_label || event.logger || "").replace(" (home)", "");
  const title = event.detail || eventLabel(event.type, event.subtype);
  return (
    <button
      type="button"
      className={`flex w-full items-start justify-between gap-3 rounded-xl border px-3 py-3 text-left ${cardTone(event)}`}
      onClick={() => event.raw_transcript && onOpenQuote?.(event)}
    >
      <span className="min-w-0">
        <span className="block text-[15px] font-bold leading-snug">{title}</span>
        <span className="mt-0.5 block text-[12px] text-ink">
          {eventLabel(event.type, event.subtype)}
          {who ? ` · ${who}` : ""}
        </span>
      </span>
      <span className="shrink-0 text-right">
        <span className="block text-[15px] font-bold tabular-nums">{clock(event.event_time)}</span>
      </span>
    </button>
  );
}

function Block({ title, children }) {
  return (
    <div className="rounded-xl border border-line bg-paper px-3 py-3">
      {title ? <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{title}</p> : null}
      <div className={title ? "mt-2" : ""}>{children}</div>
    </div>
  );
}

function Timeline({ rows, onOpenQuote, empty }) {
  if (!rows.length) {
    return <p className="text-[15px] text-muted">{empty}</p>;
  }
  return (
    <ul className="space-y-2">
      {rows.map((event) => (
        <li key={event.id}>
          <LogCard event={event} onOpenQuote={onOpenQuote} />
        </li>
      ))}
    </ul>
  );
}

function StabilityChart({ days }) {
  const rows = days || [];
  if (!rows.length) return null;
  const max = Math.max(1, ...rows.map((day) => day.issues || 0));
  return (
    <div>
      <div className="flex h-28 items-end gap-1">
        {rows.map((day) => {
          const issues = day.issues || 0;
          const stable = Boolean(day.stable) && issues === 0;
          const height = stable ? 100 : Math.max(18, Math.round((issues / max) * 100));
          return (
            <div key={day.date} className="flex min-w-0 flex-1 flex-col items-center gap-1">
              <div
                className={`w-full rounded-t-md ${stable ? "bg-[#007f3b]" : "bg-[#d5281b]"}`}
                style={{ height: `${height}%` }}
                title={stable ? `${day.label}: stable` : `${day.label}: ${issues} issue${issues === 1 ? "" : "s"}`}
              />
              <span className="text-[11px] font-semibold text-muted">{day.label}</span>
            </div>
          );
        })}
      </div>
      <p className="mt-2 text-[12px] text-muted">Green is a quiet day. Red is falls, vomiting, confusion, late tablets, low appetite, low mood or a bad night.</p>
    </div>
  );
}

function MonthCal({ cursor, events, selected, onSelect, onPrev, onNext }) {
  const marked = useMemo(() => {
    const logs = new Set();
    const issues = new Set();
    (events || []).forEach((event) => {
      const at = new Date(event.event_time);
      const key = dayKey(at);
      logs.add(key);
      if (UNSETTLED.has(event.subtype) || event.type === "incident") issues.add(key);
    });
    return { logs, issues };
  }, [events]);

  const year = cursor.getFullYear();
  const month = cursor.getMonth();
  const first = new Date(year, month, 1);
  const startPad = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells = [];
  for (let i = 0; i < startPad; i += 1) cells.push(null);
  for (let day = 1; day <= daysInMonth; day += 1) cells.push(new Date(year, month, day));

  const label = cursor.toLocaleDateString("en-GB", { month: "long", year: "numeric" });
  const selectedKey = selected ? dayKey(selected) : "";

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <button type="button" className="px-2 text-lg font-bold text-accent" onClick={onPrev} aria-label="Previous month">
          ‹
        </button>
        <p className="text-[15px] font-bold capitalize">{label}</p>
        <button type="button" className="px-2 text-lg font-bold text-accent" onClick={onNext} aria-label="Next month">
          ›
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-semibold text-muted">
        {WEEKDAYS.map((name, index) => (
          <span key={`${name}-${index}`}>{name}</span>
        ))}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1">
        {cells.map((date, index) => {
          if (!date) return <span key={`e-${index}`} />;
          const key = dayKey(date);
          const has = marked.logs.has(key);
          const rough = marked.issues.has(key);
          const on = key === selectedKey;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelect(date)}
              className={`flex h-9 flex-col items-center justify-center rounded-lg text-[13px] ${
                on ? "bg-accent font-bold text-paper" : rough ? "bg-[#f8d7d4] font-bold text-ink" : has ? "font-bold text-ink" : "text-muted"
              }`}
            >
              {date.getDate()}
              {has && !on ? <span className={`mt-0.5 h-1 w-1 rounded-full ${rough ? "bg-danger" : "bg-accent"}`} /> : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function PersonScreen({ profile, events, view, onOpenQuote, showPages, onBrief, canWrite, onRecord }) {
  const [askOpen, setAskOpen] = useState(false);
  const [dayTab, setDayTab] = useState("today");
  const [cursor, setCursor] = useState(() => new Date());
  const [picked, setPicked] = useState(null);
  const now = new Date();
  const yesterday = useMemo(() => {
    const d = new Date(now);
    d.setDate(d.getDate() - 1);
    return d;
  }, [now]);

  const todayRows = useMemo(
    () => (events || []).filter((event) => sameDay(event.event_time, now)).sort((a, b) => a.event_time.localeCompare(b.event_time)),
    [events],
  );
  const yesterdayRows = useMemo(
    () => (events || []).filter((event) => sameDay(event.event_time, yesterday)).sort((a, b) => a.event_time.localeCompare(b.event_time)),
    [events, yesterday],
  );
  const pickedRows = useMemo(() => {
    if (!picked) return [];
    return (events || [])
      .filter((event) => sameDay(event.event_time, picked))
      .sort((a, b) => a.event_time.localeCompare(b.event_time));
  }, [events, picked]);

  const pickedKey = picked ? dayKey(picked) : "";
  const pickedLabel = picked
    ? picked.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" })
    : "";
  const pickedBrief = pickedKey ? view?.day_briefs?.[pickedKey] : "";
  const name = profile?.name || "them";
  const tabRows = dayTab === "today" ? todayRows : yesterdayRows;
  const tabEmpty = dayTab === "today" ? "Nothing spoken today yet. Record an activity." : "Nothing spoken yesterday.";

  return (
    <section className="space-y-3 pb-4">
      <div className="flex items-center gap-3">
        <Avatar name={profile?.name} size="lg" />
        <div className="min-w-0">
          <h2 className="text-[1.75rem] font-bold leading-tight">{profile?.name || "Person"}</h2>
          <p className="text-[13px] text-muted">{profile?.usual || (profile?.age ? `Age ${profile.age}` : "")}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          className={`rounded-xl border px-3 py-3 text-[15px] font-bold ${askOpen ? "border-accent bg-soft text-accent" : "border-line bg-paper"}`}
          onClick={() => setAskOpen((value) => !value)}
        >
          Ask about {name}
        </button>
        {canWrite && onRecord ? (
          <button type="button" className="rounded-xl bg-button px-3 py-3 text-[15px] font-bold text-paper" onClick={onRecord}>
            Record activity
          </button>
        ) : (
          <span className="rounded-xl border border-line bg-soft px-3 py-3 text-[13px] text-muted">View only</span>
        )}
      </div>
      {askOpen ? (
        <Block>
          <AskNotes name={name} onOpenQuote={onOpenQuote} />
        </Block>
      ) : null}

      <Block title={`7 days with ${name}`}>
        <p className="text-[15px] leading-relaxed">{view?.week_summary || "Nothing spoken in the last 7 days."}</p>
        <p className="mt-2 text-[12px] text-muted">
          {view?.drafted ? "Written from the spoken notes. Not a diagnosis." : "Writing the briefing from the notes…"}
        </p>
      </Block>

      <Block title="Essentials this week">
        <div className="grid grid-cols-2 gap-2">
          {(view?.essentials || []).map((item) => (
            <div key={item.key} className={`rounded-lg px-3 py-2 ${item.count ? "bg-[#fff2cc]" : "bg-soft"}`}>
              <p className="text-[22px] font-bold tabular-nums leading-none">{item.count}</p>
              <p className="mt-1 text-[12px] font-semibold text-ink">{item.label}</p>
            </div>
          ))}
        </div>
      </Block>

      <Block title="How stable this week">
        <StabilityChart days={view?.stability} />
      </Block>

      <Block title="Activities from voice">
        <div className="mb-3 grid grid-cols-2 gap-1 rounded-lg bg-soft p-1">
          <button
            type="button"
            className={`rounded-md py-2 text-[13px] font-bold ${dayTab === "today" ? "bg-paper text-accent shadow-sm" : "text-muted"}`}
            onClick={() => setDayTab("today")}
          >
            Today{todayRows.length ? ` · ${todayRows.length}` : ""}
          </button>
          <button
            type="button"
            className={`rounded-md py-2 text-[13px] font-bold ${dayTab === "yesterday" ? "bg-paper text-accent shadow-sm" : "text-muted"}`}
            onClick={() => setDayTab("yesterday")}
          >
            Yesterday{yesterdayRows.length ? ` · ${yesterdayRows.length}` : ""}
          </button>
        </div>
        {dayTab === "yesterday" && view?.yesterday_summary ? (
          <p className="mb-3 text-[14px] leading-relaxed text-ink">{view.yesterday_summary}</p>
        ) : null}
        <Timeline rows={tabRows} onOpenQuote={onOpenQuote} empty={tabEmpty} />
      </Block>

      <Block title="Calendar">
        <p className="mb-2 text-[13px] text-muted">Tap a day for that day’s summary and timeline. Pink days had a fall, vomit, confusion or late tablets.</p>
        <MonthCal
          cursor={cursor}
          events={events}
          selected={picked}
          onSelect={setPicked}
          onPrev={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}
          onNext={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}
        />
        {picked ? (
          <div className="mt-3 border-t border-line pt-3">
            <p className="mb-1 text-[15px] font-bold">{pickedLabel}</p>
            <p className="mb-3 text-[14px] leading-relaxed">{pickedBrief || (pickedRows.length ? `${pickedRows.length} notes that day.` : "Nothing spoken that day.")}</p>
            <Timeline rows={pickedRows} onOpenQuote={onOpenQuote} empty="Nothing spoken that day." />
          </div>
        ) : null}
      </Block>

      {showPages ? (
        <button type="button" className="text-[13px] font-semibold text-accent" onClick={onBrief}>
          GP page
        </button>
      ) : null}
    </section>
  );
}
