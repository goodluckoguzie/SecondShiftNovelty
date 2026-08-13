import { useEffect, useRef, useState } from "react";
import { getJson, getPersonId, postJson, setDemoRole, setPersonId, speak, transcribeAudio } from "./api.js";
import { QuoteCard } from "./components/QuoteCard.jsx";
import { Shell } from "./components/Shell.jsx";
import { BriefScreen } from "./screens/BriefScreen.jsx";
import { EmergencyScreen } from "./screens/EmergencyScreen.jsx";
import { PatternsScreen } from "./screens/PatternsScreen.jsx";
import { PersonPick } from "./screens/PersonPick.jsx";
import { RoleGate } from "./screens/RoleGate.jsx";
import { TalkScreen } from "./screens/TalkScreen.jsx";
import { TimelineScreen } from "./screens/TimelineScreen.jsx";

export default function App() {
  const [step, setStep] = useState("who");
  const [role, setRole] = useState(null);
  const [worker, setWorker] = useState(null);
  const [tab, setTab] = useState("Talk");
  const [people, setPeople] = useState([]);
  const [workers, setWorkers] = useState([]);
  const [profile, setProfile] = useState(null);
  const [events, setEvents] = useState([]);
  const [flags, setFlags] = useState([]);
  const [chart, setChart] = useState({ days: [], dose_change: null });
  const [transcript, setTranscript] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [similar, setSimilar] = useState([]);
  const [emergency, setEmergency] = useState(null);
  const [quote, setQuote] = useState(null);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [briefMd, setBriefMd] = useState("");
  const [handoverMd, setHandoverMd] = useState("");
  const [error, setError] = useState("");
  const [urgent, setUrgent] = useState(false);
  const [shift, setShift] = useState(null);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const autoStopRef = useRef(null);
  const applyLogRef = useRef(null);

  function hasNativeMic() {
    return Boolean(window.ReactNativeWebView?.postMessage || window.__SECOND_SHIFT_NATIVE__);
  }

  const canWrite = role === "support_worker";
  const whoLabel = worker?.display_name || "Nurse or GP";
  const homeTab = canWrite ? "Talk" : "Timeline";
  const backLabel = canWrite ? "Back to log" : "Back to history";
  function goHome() {
    setTab(homeTab);
  }

  useEffect(() => {
    Promise.all([getJson("/people"), getJson("/users")])
      .then(([list, users]) => {
        setPeople(list);
        setWorkers(users.filter((u) => u.role === "support_worker"));
      })
      .catch((err) => setError(err.message));
  }, []);

  async function refresh() {
    const [list, p, e, f, c] = await Promise.all([
      getJson("/people"),
      getJson("/profile"),
      getJson("/events"),
      getJson("/flags"),
      getJson("/patterns"),
    ]);
    setPeople(list);
    setProfile(p);
    setEvents(e);
    setFlags(f);
    setChart(c);
  }

  function resetPersonState() {
    setBriefMd("");
    setHandoverMd("");
    setSimilar([]);
    setConfirmation("");
    setQuote(null);
    setTranscript("");
    setError("");
  }

  function chooseWorker(nextWorker) {
    setWorker(nextWorker);
    setRole("support_worker");
    setDemoRole("support_worker");
    setTab("Talk");
    setShift(null);
    setPersonId(null);
    setProfile(null);
    resetPersonState();
    setStep("person");
  }

  function chooseClinical() {
    setWorker(null);
    setRole("clinician");
    setDemoRole("clinician");
    setTab("Timeline");
    setShift(null);
    setPersonId(null);
    setProfile(null);
    resetPersonState();
    setStep("person");
  }

  async function choosePerson(person) {
    setPersonId(person.id);
    resetPersonState();
    setBusy(true);
    try {
      await refresh();
      setStep("app");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function applyLog(result) {
    if (result.emergency) {
      setEmergency(result.screen);
      speak("Call 999 now.");
      return;
    }
    setEmergency(null);
    setConfirmation(result.confirmation);
    setSimilar(result.similar || []);
    speak(result.confirmation);
    await refresh();
  }
  applyLogRef.current = applyLog;

  useEffect(() => {
    function onNative(event) {
      const data = event.detail || {};
      if (data.type === "mic-saving") {
        setBusy(true);
        setRecording(false);
        setStatus("writing");
        return;
      }
      if (data.type === "mic-heard") {
        setBusy(true);
        setRecording(false);
        setStatus("saving");
        if (data.transcript) setTranscript(data.transcript);
        return;
      }
      if (data.type === "mic-error") {
        setBusy(false);
        setRecording(false);
        setStatus("");
        setError(data.message || "Microphone failed. Type the log instead.");
        return;
      }
      if (data.type === "mic-result" && data.result) {
        if (data.transcript) setTranscript(data.transcript);
        applyLogRef.current(data.result).finally(() => {
          setBusy(false);
          setRecording(false);
          setStatus("");
        });
      }
    }
    window.addEventListener("secondshift-native", onNative);
    return () => window.removeEventListener("secondshift-native", onNative);
  }, []);

  async function submitTranscript(text) {
    setBusy(true);
    setError("");
    try {
      const result = await postJson("/log", {
        transcript: text,
        urgent,
        use_heuristic: false,
        shift_id: shift?.id,
        logger_id: worker?.id,
      });
      await applyLog(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function cleanupMic() {
    if (autoStopRef.current) {
      clearTimeout(autoStopRef.current);
      autoStopRef.current = null;
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }

  async function startMic() {
    setError("");
    setConfirmation("");
    setTranscript("");
    setStatus("");
    if (hasNativeMic()) {
      window.ReactNativeWebView?.postMessage(
        JSON.stringify({
          type: "mic-start",
          person_id: getPersonId(),
          logger_id: worker?.id,
          shift_id: shift?.id,
          urgent,
        }),
      );
      setRecording(true);
      autoStopRef.current = setTimeout(() => stopMic(), 15000);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This screen cannot use the microphone. Type the log instead.");
      return;
    }
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
      recorder.onstop = async () => {
        cleanupMic();
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (blob.size < 1000) {
          setError("That was too short. Press to speak, talk, then press to stop.");
          setRecording(false);
          return;
        }
        setBusy(true);
        setStatus("writing");
        try {
          const heard = await transcribeAudio(blob);
          const text = (heard.transcript || "").trim();
          if (!text) {
            setError("Heard nothing. Speak again, then press Stop.");
            return;
          }
          setTranscript(text);
          setStatus("saving");
          const result = await postJson("/log", {
            transcript: text,
            urgent,
            use_heuristic: true,
            shift_id: shift?.id,
            logger_id: worker?.id,
          });
          result.transcript = text;
          await applyLog(result);
        } catch (err) {
          setError(`Could not write what you said. Type the log instead. ${err.message}`);
        } finally {
          setBusy(false);
          setRecording(false);
          setStatus("");
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

  function stopMic() {
    if (autoStopRef.current) {
      clearTimeout(autoStopRef.current);
      autoStopRef.current = null;
    }
    if (hasNativeMic()) {
      window.ReactNativeWebView?.postMessage(JSON.stringify({ type: "mic-stop" }));
      return;
    }
    const recorder = mediaRef.current;
    if (recorder && recorder.state !== "inactive") recorder.stop();
    setRecording(false);
  }

  async function ensureShift() {
    if (shift?.id) return shift;
    const created = await postJson("/shifts", { user_id: worker?.id });
    setShift(created);
    return created;
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

  async function makeHandover(windowKind) {
    setBusy(true);
    try {
      let shiftId = shift?.id;
      if (windowKind === "shift") {
        const current = await ensureShift();
        shiftId = current.id;
      }
      const result = await postJson("/handover", {
        name: windowKind === "shift" ? whoLabel : "your sister",
        window: windowKind,
        shift_id: shiftId,
      });
      setHandoverMd(result.markdown);
      setTab("Brief");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (emergency) {
    return <EmergencyScreen message={emergency} onBack={() => setEmergency(null)} />;
  }

  if (step === "who") {
    return (
      <RoleGate workers={workers} onChooseWorker={chooseWorker} onChooseClinical={chooseClinical} />
    );
  }

  if (step === "person") {
    return (
      <PersonPick
        people={people}
        whoLabel={whoLabel}
        onBack={() => setStep("who")}
        onChoose={choosePerson}
        busy={busy}
      />
    );
  }

  return (
    <Shell
      profile={profile}
      people={people}
      whoLabel={whoLabel}
      tab={tab}
      onTab={setTab}
      hiddenTabs={canWrite ? [] : ["Talk"]}
      viewOnly={!canWrite}
      onPickPerson={async (id) => {
        const person = people.find((p) => p.id === id);
        if (person) await choosePerson(person);
      }}
      onSwitchWho={() => {
        setRole(null);
        setWorker(null);
        setPersonId(null);
        setProfile(null);
        setDemoRole("support_worker");
        setStep("who");
      }}
    >
      {error && <p className="nhs-error text-base leading-relaxed">{error}</p>}
      <QuoteCard quote={quote} onClose={() => setQuote(null)} />
      {tab === "Talk" && (
        <TalkScreen
          canWrite={canWrite}
          transcript={transcript}
          setTranscript={setTranscript}
          recording={recording}
          busy={busy}
          status={status}
          confirmation={confirmation}
          similar={similar}
          flags={flags}
          urgent={urgent}
          setUrgent={setUrgent}
          onStart={startMic}
          onStop={stopMic}
          onLog={() => submitTranscript(transcript)}
          onOpenQuote={setQuote}
          onOpenWatch={() => setTab("Patterns")}
        />
      )}
      {tab === "Timeline" && <TimelineScreen events={events} onOpenQuote={setQuote} />}
      {tab === "Patterns" && (
        <PatternsScreen
          personName={profile?.name}
          chart={chart}
          flags={flags}
          onOpenQuote={setQuote}
          onBack={goHome}
          backLabel={backLabel}
        />
      )}
      {tab === "Brief" && (
        <BriefScreen
          busy={busy}
          briefMd={briefMd}
          handoverMd={handoverMd}
          hasBrief={Boolean(briefMd)}
          hasHandover={Boolean(handoverMd)}
          onBrief={makeBrief}
          onHandoverShift={() => makeHandover("shift")}
          onHandoverFamily={() => makeHandover("72h")}
          canWriteShift={canWrite}
        />
      )}
    </Shell>
  );
}
