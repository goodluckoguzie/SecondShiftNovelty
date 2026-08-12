import { useEffect, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getJson, pdfUrl, postJson, speak, transcribeBlob } from "./api.js";

const TABS = ["Talk", "Timeline", "Patterns", "Brief"];

export default function App() {
  const [tab, setTab] = useState("Talk");
  const [profile, setProfile] = useState(null);
  const [events, setEvents] = useState([]);
  const [flags, setFlags] = useState([]);
  const [chart, setChart] = useState({ days: [], dose_change: null });
  const [transcript, setTranscript] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [emergency, setEmergency] = useState(null);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [briefMd, setBriefMd] = useState("");
  const [handoverMd, setHandoverMd] = useState("");
  const [error, setError] = useState("");
  const [urgent, setUrgent] = useState(false);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const autoStopRef = useRef(null);

  async function refresh() {
    const [p, e, f, c] = await Promise.all([
      getJson("/profile"),
      getJson("/events"),
      getJson("/flags"),
      getJson("/patterns"),
    ]);
    setProfile(p);
    setEvents(e);
    setFlags(f);
    setChart(c);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  async function submitTranscript(text, markUrgent = urgent) {
    setBusy(true);
    setError("");
    try {
      const result = await postJson("/log", { transcript: text, urgent: markUrgent, use_heuristic: false });
      if (result.emergency) {
        setEmergency(result.screen);
        speak("Call 999 now.");
        return;
      }
      setEmergency(null);
      setConfirmation(result.confirmation);
      speak(result.confirmation);
      await refresh();
      setTab("Timeline");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function startMic() {
    setError("");
    setConfirmation("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const types = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg"];
      const mime = types.find((t) => window.MediaRecorder?.isTypeSupported(t)) || "";
      const recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size) chunksRef.current.push(ev.data);
      };
      recorder.onerror = () => {
        setError("Microphone recorder failed. Type the log instead.");
        cleanupMic();
      };
      recorder.onstop = async () => {
        cleanupMic(false);
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (blob.size < 1000) {
          setError("Recording was too short. Press Start, speak, then press Stop.");
          setRecording(false);
          return;
        }
        setBusy(true);
        try {
          const { transcript: text } = await transcribeBlob(blob);
          if (!text) {
            setError("Heard nothing. Type the log instead.");
            return;
          }
          setTranscript(text);
          await submitTranscript(text);
        } catch (err) {
          setError(`Whisper failed. Type the log instead. ${err.message}`);
        } finally {
          setBusy(false);
          setRecording(false);
        }
      };
      mediaRef.current = recorder;
      recorder.start(250);
      setRecording(true);
      autoStopRef.current = setTimeout(() => stopMic(), 15000);
    } catch (err) {
      setRecording(false);
      setError(
        err.name === "NotAllowedError"
          ? "Microphone blocked. Allow mic in the browser, or type the log below."
          : `Microphone failed (${err.message}). Type the log below.`
      );
    }
  }

  function cleanupMic(stopTracks = true) {
    if (autoStopRef.current) {
      clearTimeout(autoStopRef.current);
      autoStopRef.current = null;
    }
    if (stopTracks) {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    } else {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }

  function stopMic() {
    const recorder = mediaRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    setRecording(false);
  }

  async function makeBrief() {
    setBusy(true);
    try {
      const result = await postJson("/briefs", {});
      setBriefMd(result.markdown);
      setTab("Brief");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function makeHandover() {
    setBusy(true);
    try {
      const result = await postJson("/handover", { name: "your sister" });
      setHandoverMd(result.markdown);
      setTab("Brief");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (emergency) {
    return (
      <div className="min-h-screen bg-red-800 text-white flex items-center justify-center p-6">
        <div className="max-w-md text-center space-y-4">
          <p className="uppercase tracking-widest text-sm">Emergency</p>
          <h1 className="text-3xl font-bold">Call 999 now</h1>
          <p>{emergency}</p>
          <p className="text-sm opacity-80">Second Shift does not use AI for this. If it is not an emergency, call NHS 111.</p>
          <button className="bg-white text-red-800 px-4 py-2 rounded-lg font-semibold" onClick={() => setEmergency(null)}>
            Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen max-w-md mx-auto bg-white shadow-xl flex flex-col">
      <header className="p-4 border-b border-slate-200">
        <p className="text-xs uppercase tracking-widest text-accent font-bold">Second Shift</p>
        <h1 className="text-xl font-semibold">
          Caring for {profile?.name || "Dad"} · {profile?.conditions || "dementia"}
        </h1>
        <p className="text-xs text-muted mt-1">{profile?.disclaimer}</p>
      </header>

      <main className="flex-1 p-4 space-y-4 overflow-auto">
        {error && <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded p-2">{error}</p>}
        {busy && <p className="text-sm text-accent">Working…</p>}

        {tab === "Talk" && (
          <section className="space-y-3">
            <button
              type="button"
              className={`w-28 h-28 rounded-full mx-auto block text-white text-lg font-bold ${recording ? "bg-red-600" : "bg-accent"}`}
              onClick={recording ? stopMic : startMic}
              disabled={busy}
            >
              {recording ? "Stop" : "Start"}
            </button>
            <p className="text-center text-sm text-muted">
              {recording
                ? "Recording… click Stop when you finish speaking (auto-stops after 15s)."
                : busy
                  ? "Transcribing and logging…"
                  : "Click Start, speak, then click Stop. Or type below if the mic fails."}
            </p>
            <textarea
              className="w-full border rounded-lg p-3 text-sm min-h-[90px]"
              placeholder="Gave dad his 8pm meds, 40 minutes late. More confused again this evening, third time this week."
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
            />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={urgent} onChange={(e) => setUrgent(e.target.checked)} />
              Add to the urgent section of the GP brief
            </label>
            <button
              className="w-full bg-accent text-white rounded-lg py-2 font-semibold"
              onClick={() => submitTranscript(transcript)}
              disabled={!transcript.trim() || busy}
            >
              Log text
            </button>
            {confirmation && <p className="text-sm bg-soft border rounded-lg p-3">{confirmation}</p>}
            <p className="text-xs text-muted">If you are worried and it is not an emergency, call NHS 111.</p>
          </section>
        )}

        {tab === "Timeline" && (
          <section className="space-y-2">
            {events.map((event) => (
              <article key={event.id} className="border rounded-lg p-3">
                <p className="text-xs text-muted">{new Date(event.event_time).toLocaleString("en-GB")}</p>
                <p className="font-semibold text-sm">
                  {event.type} · {event.subtype}
                </p>
                <p className="text-sm">{event.detail}</p>
                {event.raw_transcript && <p className="text-xs text-muted mt-1">“{event.raw_transcript}”</p>}
              </article>
            ))}
          </section>
        )}

        {tab === "Patterns" && (
          <section className="space-y-3">
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chart.days}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="confusion" fill="#1e5f8a" />
                  {chart.dose_change && (
                    <ReferenceLine x={new Date(chart.dose_change).toLocaleDateString("en-GB", { weekday: "short" })} stroke="#b45309" label="dose change" />
                  )}
                </BarChart>
              </ResponsiveContainer>
            </div>
            <ul className="text-sm space-y-1">
              {flags.map((flag) => (
                <li key={flag.id || flag.message} className="bg-orange-50 border border-orange-200 rounded p-2">
                  {flag.message}
                </li>
              ))}
            </ul>
            <p className="text-xs text-muted">The LLM describes this. A rules engine counts it.</p>
          </section>
        )}

        {tab === "Brief" && (
          <section className="space-y-3">
            <button className="w-full bg-accent text-white rounded-lg py-2 font-semibold" onClick={makeBrief} disabled={busy}>
              Generate GP brief
            </button>
            <button className="w-full border border-accent text-accent rounded-lg py-2 font-semibold" onClick={makeHandover} disabled={busy}>
              Family handover (72 hours)
            </button>
            <a className="block text-center text-sm text-accent underline" href={pdfUrl("gp")} target="_blank" rel="noreferrer">
              Download GP PDF
            </a>
            <a className="block text-center text-sm text-accent underline" href={pdfUrl("handover")} target="_blank" rel="noreferrer">
              Download handover PDF
            </a>
            <pre className="whitespace-pre-wrap text-xs bg-soft p-3 rounded-lg max-h-80 overflow-auto">
              {briefMd || handoverMd || "Generate a brief to preview it here."}
            </pre>
          </section>
        )}
      </main>

      <nav className="grid grid-cols-4 border-t text-xs">
        {TABS.map((name) => (
          <button
            key={name}
            className={`py-3 ${tab === name ? "text-accent font-bold" : "text-muted"}`}
            onClick={() => setTab(name)}
          >
            {name}
          </button>
        ))}
      </nav>
    </div>
  );
}
