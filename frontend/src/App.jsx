import { useEffect, useRef, useState } from "react";
import { getJson, getPersonId, patchJson, postJson, setDemoRole, setPersonId, speak, speakFailMessage, transcribeAudio } from "./api.js";
import { extractPattern } from "./labels.js";
import { QuoteCard } from "./components/QuoteCard.jsx";
import { Shell } from "./components/Shell.jsx";
import { AdminScreen } from "./screens/AdminScreen.jsx";
import { BoardScreen } from "./screens/BoardScreen.jsx";
import { BriefScreen } from "./screens/BriefScreen.jsx";
import { EmergencyScreen } from "./screens/EmergencyScreen.jsx";
import { HandOnSheet } from "./screens/HandOnSheet.jsx";
import { PatternSheet } from "./screens/PatternSheet.jsx";
import { PersonScreen } from "./screens/PersonScreen.jsx";
import { RoleGate } from "./screens/RoleGate.jsx";
import { SpeakOverlay } from "./screens/SpeakOverlay.jsx";
import { WhoAbout } from "./screens/WhoAbout.jsx";

export default function App() {
  const [step, setStep] = useState("who");
  const [role, setRole] = useState(null);
  const [worker, setWorker] = useState(null);
  const [tab, setTab] = useState("Board");
  const [people, setPeople] = useState([]);
  const [workers, setWorkers] = useState([]);
  const [profile, setProfile] = useState(null);
  const [board, setBoard] = useState({ people: [] });
  const [events, setEvents] = useState([]);
  const [flags, setFlags] = useState([]);
  const [chart, setChart] = useState({ days: [], dose_change: null });
  const [transcript, setTranscript] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [warning, setWarning] = useState("");
  const [slices, setSlices] = useState([]);
  const [speakAbout, setSpeakAbout] = useState("wing");
  const [guess, setGuess] = useState("");
  const [similar, setSimilar] = useState([]);
  const [emergency, setEmergency] = useState(null);
  const [quote, setQuote] = useState(null);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [briefMd, setBriefMd] = useState("");
  const [handoverMd, setHandoverMd] = useState("");
  const [pageKind, setPageKind] = useState("gp");
  const [error, setError] = useState("");
  const [urgent, setUrgent] = useState(false);
  const [shift, setShift] = useState(null);
  const [speakOpen, setSpeakOpen] = useState(false);
  const [pickOpen, setPickOpen] = useState(false);
  const [pickHint, setPickHint] = useState("");
  const [pendingTranscript, setPendingTranscript] = useState("");
  const [patternHit, setPatternHit] = useState(null);
  const [patternOpen, setPatternOpen] = useState(false);
  const [handOpen, setHandOpen] = useState(false);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const autoStopRef = useRef(null);
  const applyLogRef = useRef(null);
  const corridorRef = useRef(false);
  const confirmCorridorRef = useRef(null);
  const refreshRef = useRef(null);
  const cancelledRef = useRef(false);
  const speakAboutRef = useRef("wing");
  const finishSpeakRef = useRef(null);
  const heardRef = useRef("");

  function hasNativeMic() {
    return Boolean(window.ReactNativeWebView?.postMessage || window.__SECOND_SHIFT_NATIVE__);
  }

  const canWrite = role === "support_worker" || role === "family";
  const isFamily = role === "family";
  const isAdmin = role === "admin";
  const whoLabel = worker?.display_name || (isFamily ? "Family" : isAdmin ? "Admin" : "Nurse or GP");

  async function reloadDirectory() {
    const [list, users] = await Promise.all([getJson("/people"), getJson("/users")]);
    setPeople(list);
    setWorkers(users.filter((u) => u.role === "support_worker"));
    return users;
  }

  useEffect(() => {
    reloadDirectory().catch((err) => setError(err.message));
  }, []);

  async function refresh(asRole) {
    const current = asRole || role;
    const list = await getJson("/people");
    setPeople(list);
    if (current !== "family") {
      try {
        setBoard(await getJson("/board"));
      } catch (_err) {
        setBoard({ people: [] });
      }
    }
    if (!getPersonId()) {
      setProfile(null);
      setEvents([]);
      setFlags([]);
      return;
    }
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
  refreshRef.current = refresh;
  speakAboutRef.current = speakAbout;

  function resetCapture() {
    setBriefMd("");
    setHandoverMd("");
    setSimilar([]);
    setConfirmation("");
    setWarning("");
    setGuess("");
    setQuote(null);
    setTranscript("");
    setSlices([]);
    setError("");
    setPatternOpen(false);
    setHandOpen(false);
  }

  async function chooseWorker(nextWorker, password) {
    setBusy(true);
    setError("");
    try {
      const authed = await postJson("/staff/login", { user_id: nextWorker.id, password });
      setWorker(authed);
      setRole("support_worker");
      setDemoRole("support_worker");
      setShift(null);
      setSpeakAbout("wing");
      resetCapture();
      const assignedId = authed.assigned_person_id;
      if (assignedId) setPersonId(assignedId);
      else {
        setPersonId(null);
        setProfile(null);
      }
      setTab("Board");
      await refresh("support_worker");
      setStep("app");
    } catch (err) {
      setError(err.message === "Wrong password." ? "Wrong password." : err.message);
    } finally {
      setBusy(false);
    }
  }

  function chooseClinical() {
    setWorker(null);
    setRole("clinician");
    setDemoRole("clinician");
    setTab("Board");
    setShift(null);
    setSpeakAbout("wing");
    setPersonId(null);
    setProfile(null);
    resetCapture();
    setStep("app");
  }

  async function chooseAdmin(password) {
    setBusy(true);
    setError("");
    try {
      await postJson("/admin/login", { password });
      setWorker(null);
      setRole("admin");
      setDemoRole("admin");
      setPersonId(null);
      setProfile(null);
      resetCapture();
      await reloadDirectory();
      setStep("admin");
    } catch (_err) {
      setError("Wrong password.");
    } finally {
      setBusy(false);
    }
  }

  async function chooseFamily(person, password) {
    setBusy(true);
    setError("");
    try {
      const authed = await postJson("/family/login", { person_id: person.id, password });
      const dadId = authed.family_person_id || person.id;
      setWorker(authed);
      setRole("family");
      setDemoRole("family");
      setSpeakAbout(dadId);
      setTab("Person");
      setShift(null);
      resetCapture();
      setPersonId(dadId);
      await refresh("family");
      setStep("app");
    } catch (err) {
      setError(err.message === "Wrong password." ? "Wrong password." : err.message);
    } finally {
      setBusy(false);
    }
  }

  async function choosePerson(person, keepPattern = false) {
    if (!keepPattern) setPatternHit(null);
    setPersonId(person.id);
    setSpeakAbout(person.id);
    resetCapture();
    setBusy(true);
    try {
      await refresh();
      setTab("Person");
      setStep("app");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function handleTab(next) {
    if (speakOpen || recording || patternOpen || handOpen) return;
    if (next === "Talk") {
      if (role === "clinician") return;
      const about = isFamily || tab === "Person" ? profile?.id || speakAbout : "wing";
      openSpeak(about || "wing");
      return;
    }
    if (next === "Person") {
      if (!getPersonId()) {
        setPickHint("Pick who you are with.");
        setPendingTranscript("");
        setPickOpen(true);
        return;
      }
    }
    setTab(next);
  }

  function openSpeak(about) {
    const next = about || "wing";
    speakAboutRef.current = next;
    setSpeakAbout(next);
    cancelledRef.current = false;
    setError("");
    setConfirmation("");
    setWarning("");
    setTranscript("");
    setSlices([]);
    setSpeakOpen(true);
    startMic(next);
  }

  function speakAboutThisPerson() {
    if (!profile?.id) return;
    openSpeak(profile.id);
  }

  function goBack() {
    if (tab === "Brief") {
      setTab("Person");
      return;
    }
    setTab("Board");
  }

  useEffect(() => {
    if (step !== "app") return;
    refresh().catch((err) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, role]);

  function confirmCorridor(result) {
    const list = result.slices || [];
    const names = list.map((s) => s.person_name).filter(Boolean).join(", ");
    const message = names ? `Saved for ${names}.` : `Logged ${list.length} people.`;
    setSlices(list);
    setConfirmation(message);
    setWarning(result.warning ? `Not saved (no name): ${result.warning}` : "");
    speak(message);
    return message;
  }
  confirmCorridorRef.current = confirmCorridor;

  async function finishSpeak(result) {
    const hit = extractPattern(result, profile?.name);
    if (hit) {
      if (!hit.personId && speakAboutRef.current !== "wing") hit.personId = speakAboutRef.current;
      if (!hit.personName) hit.personName = profile?.name || "";
      setPatternHit(hit);
      setSpeakOpen(false);
      setPatternOpen(true);
      return;
    }
    const list = result?.slices || [];
    if (list.length === 1 && list[0].person_id) {
      setSpeakOpen(false);
      await choosePerson({ id: list[0].person_id, name: list[0].person_name });
      return;
    }
    if (list.length > 1) {
      setSpeakOpen(false);
      setPickHint(
        `Saved for ${list.map((s) => s.person_name).filter(Boolean).join(", ")}. Who do you want to open?`,
      );
      setPendingTranscript("");
      setPickOpen(true);
      return;
    }
    setSpeakOpen(false);
    if (speakAboutRef.current && speakAboutRef.current !== "wing") setTab("Person");
  }
  finishSpeakRef.current = finishSpeak;

  async function applyLog(result) {
    if (result.emergency) {
      setSpeakOpen(false);
      setEmergency(result.screen);
      speak("Call 999 now.");
      return;
    }
    setEmergency(null);
    setConfirmation(result.confirmation);
    setGuess(result.guess || "");
    setSimilar(result.similar || []);
    setSlices(result.slices || []);
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
        if (data.transcript) {
          heardRef.current = data.transcript;
          setTranscript(data.transcript);
        }
        return;
      }
      if (data.type === "mic-cancelled") {
        setBusy(false);
        setRecording(false);
        setStatus("");
        return;
      }
      if (data.type === "mic-error") {
        if (cancelledRef.current) return;
        setBusy(false);
        setRecording(false);
        setStatus("");
        setError(speakFailMessage(data.message));
        const message = String(data.message || "");
        if (/no names heard/i.test(message)) {
          setPendingTranscript(heardRef.current || "");
          setSpeakOpen(false);
          setPickHint("No name heard. Pick who this is about.");
          setPickOpen(true);
        }
        return;
      }
      if (data.type === "mic-result" && data.result) {
        if (cancelledRef.current) return;
        if (data.transcript) setTranscript(data.transcript);
        const result = data.result;
        if (result.slices) {
          confirmCorridorRef.current(result);
          refreshRef
            .current()
            .catch((err) => setError(err.message))
            .then(() => finishSpeakRef.current?.(result))
            .finally(() => {
              setBusy(false);
              setRecording(false);
              setStatus("");
              corridorRef.current = false;
            });
          return;
        }
        applyLogRef.current(result).then(() => finishSpeakRef.current?.(result)).finally(() => {
          setBusy(false);
          setRecording(false);
          setStatus("");
          corridorRef.current = false;
        });
      }
    }
    window.addEventListener("secondshift-native", onNative);
    return () => window.removeEventListener("secondshift-native", onNative);
  }, []);

  async function submitTranscript(text, about = speakAboutRef.current) {
    setBusy(true);
    setError("");
    try {
      if (about === "wing") {
        const result = await postJson("/log/corridor", {
          transcript: text,
          shift_id: shift?.id,
          logger_id: worker?.id,
          urgent,
          use_heuristic: false,
        });
        confirmCorridor(result);
        await refresh();
        await finishSpeak(result);
      } else {
        if (about) setPersonId(about);
        const result = await postJson("/log", {
          transcript: text,
          urgent,
          use_heuristic: false,
          shift_id: shift?.id,
          logger_id: worker?.id,
          person_id: about || undefined,
        });
        await applyLog(result);
        await finishSpeak(result);
      }
    } catch (err) {
      const message = err.message || "";
      if (about === "wing" && /no names heard/i.test(message)) {
        setPendingTranscript(text);
        setSpeakOpen(false);
        setPickHint("No name heard. Pick who this is about.");
        setPickOpen(true);
      } else {
        setError(message);
      }
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

  async function startMic(about = speakAboutRef.current) {
    cancelledRef.current = false;
    setError("");
    setConfirmation("");
    setWarning("");
    setGuess("");
    setTranscript("");
    setSlices([]);
    setStatus("");
    const corridor = about === "wing";
    corridorRef.current = corridor;
    if (hasNativeMic()) {
      window.ReactNativeWebView?.postMessage(
        JSON.stringify({
          type: "mic-start",
          mode: corridor ? "corridor" : "person",
          person_id: corridor ? null : about || getPersonId(),
          logger_id: worker?.id,
          shift_id: shift?.id,
          urgent,
          role: role || "support_worker",
        }),
      );
      setRecording(true);
      autoStopRef.current = setTimeout(() => stopMic(), 20000);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This screen cannot use the microphone. Type the log instead.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (cancelledRef.current) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
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
        if (cancelledRef.current) {
          setRecording(false);
          setBusy(false);
          setStatus("");
          corridorRef.current = false;
          return;
        }
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (blob.size < 1000) {
          setError("That was too short. Press to speak, talk, then press to stop.");
          setRecording(false);
          corridorRef.current = false;
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
          const aboutNow = speakAboutRef.current;
          if (corridorRef.current) {
            try {
              const result = await postJson("/log/corridor", {
                transcript: text,
                shift_id: shift?.id,
                logger_id: worker?.id,
                urgent,
                use_heuristic: false,
              });
              confirmCorridor(result);
              await refresh();
              await finishSpeak(result);
            } catch (err) {
              const message = err.message || "";
              if (/no names heard/i.test(message)) {
                setPendingTranscript(text);
                setSpeakOpen(false);
                setPickHint("No name heard. Pick who this is about.");
                setPickOpen(true);
              } else {
                throw err;
              }
            }
          } else {
            const result = await postJson("/log", {
              transcript: text,
              urgent,
              use_heuristic: false,
              shift_id: shift?.id,
              logger_id: worker?.id,
              person_id: aboutNow || getPersonId() || undefined,
            });
            result.transcript = text;
            await applyLog(result);
            await finishSpeak(result);
          }
        } catch (err) {
          if (!cancelledRef.current) setError(speakFailMessage(err));
        } finally {
          setBusy(false);
          setRecording(false);
          setStatus("");
          corridorRef.current = false;
        }
      };
      mediaRef.current = recorder;
      recorder.start(250);
      setRecording(true);
      autoStopRef.current = setTimeout(() => stopMic(), 20000);
    } catch (err) {
      setRecording(false);
      setError(
        err.name === "NotAllowedError"
          ? "Microphone blocked. Allow mic in the browser, or type the log below."
          : `Microphone failed (${err.message}). Type the log below.`,
      );
    }
  }

  function discardMic() {
    cancelledRef.current = true;
    if (autoStopRef.current) {
      clearTimeout(autoStopRef.current);
      autoStopRef.current = null;
    }
    if (hasNativeMic()) {
      window.ReactNativeWebView?.postMessage(JSON.stringify({ type: "mic-cancel" }));
    } else {
      const recorder = mediaRef.current;
      if (recorder && recorder.state !== "inactive") recorder.stop();
      else cleanupMic();
    }
    setRecording(false);
    setBusy(false);
    setStatus("");
  }

  function cancelSpeak() {
    discardMic();
    setSpeakOpen(false);
    setTranscript("");
    setError("");
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
      setPageKind("gp");
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
      setPageKind("handover");
      setTab("Brief");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const hiddenTabs = [];
  if (isFamily) hiddenTabs.push("Board");
  if (role === "clinician") hiddenTabs.push("Talk");

  if (emergency) {
    return <EmergencyScreen message={emergency} onBack={() => setEmergency(null)} />;
  }

  if (step === "who") {
    return (
      <RoleGate
        workers={workers}
        people={people}
        onChooseWorker={chooseWorker}
        onChooseFamily={chooseFamily}
        onChooseClinical={chooseClinical}
        onChooseAdmin={chooseAdmin}
        gateError={error}
      />
    );
  }

  if (step === "admin") {
    return (
      <AdminScreen
        people={people}
        workers={workers}
        busy={busy}
        error={error}
        onAddPerson={async (body) => {
          setBusy(true);
          setError("");
          try {
            await postJson("/admin/people", body);
            await reloadDirectory();
          } catch (err) {
            setError(err.message);
            throw err;
          } finally {
            setBusy(false);
          }
        }}
        onAddStaff={async (body) => {
          setBusy(true);
          setError("");
          try {
            await postJson("/admin/staff", body);
            await reloadDirectory();
          } catch (err) {
            setError(err.message);
            throw err;
          } finally {
            setBusy(false);
          }
        }}
        onAssign={async (userId, personId) => {
          setBusy(true);
          setError("");
          try {
            await patchJson(`/admin/staff/${userId}`, { assigned_person_id: personId });
            await reloadDirectory();
          } catch (err) {
            setError(err.message);
          } finally {
            setBusy(false);
          }
        }}
        onLeave={() => {
          setRole(null);
          setDemoRole("support_worker");
          setError("");
          setStep("who");
        }}
      />
    );
  }

  const showBack =
    !isFamily && (tab === "Person" || tab === "Brief") && !speakOpen && !pickOpen && !patternOpen && !handOpen;

  async function chooseFromPicker(person) {
    setPickOpen(false);
    const pending = pendingTranscript.trim();
    setPendingTranscript("");
    if (pending) {
      speakAboutRef.current = person.id;
      setSpeakAbout(person.id);
      await submitTranscript(pending, person.id);
      return;
    }
    await choosePerson(person);
  }

  return (
    <Shell
      whoLabel={whoLabel}
      tab={tab}
      onTab={handleTab}
      hiddenTabs={hiddenTabs}
      viewOnly={!canWrite}
      speakOpen={speakOpen}
      overlay={
        <>
          {speakOpen ? (
            <SpeakOverlay
              recording={recording}
              busy={busy}
              status={status}
              aboutName={speakAbout === "wing" ? "" : profile?.name || "this person"}
              error={error}
              transcript={transcript}
              setTranscript={setTranscript}
              onStop={stopMic}
              onCancel={cancelSpeak}
              onDiscardMic={discardMic}
              onSaveTyped={() => submitTranscript(transcript)}
            />
          ) : null}
          {pickOpen ? (
            <WhoAbout
              people={people}
              hint={pickHint}
              busy={busy}
              onChoose={chooseFromPicker}
              onCancel={() => {
                setPickOpen(false);
                setPendingTranscript("");
              }}
            />
          ) : null}
          {patternOpen ? (
            <PatternSheet
              hit={patternHit}
              onOpenQuote={setQuote}
              onOpen={async (person) => {
                setPatternOpen(false);
                await choosePerson(person, true);
              }}
              onStay={() => {
                setPatternOpen(false);
                setTab("Board");
              }}
            />
          ) : null}
          {handOpen ? (
            <HandOnSheet
              people={board.people}
              onOpen={async (row) => {
                setHandOpen(false);
                await choosePerson(row);
              }}
              onClose={() => setHandOpen(false)}
            />
          ) : null}
        </>
      }
      onBack={showBack ? goBack : undefined}
      onSwitchWho={() => {
        setRole(null);
        setWorker(null);
        setPersonId(null);
        setProfile(null);
        setDemoRole("support_worker");
        setStep("who");
      }}
    >
      {error && !speakOpen && !pickOpen && !patternOpen && !handOpen ? (
        <p className="nhs-error text-lg leading-relaxed">{error}</p>
      ) : null}
      <QuoteCard quote={quote} onClose={() => setQuote(null)} />
      {tab === "Board" && (
        <BoardScreen
          board={board}
          canWrite={canWrite && role === "support_worker"}
          onOpenPerson={(row) => choosePerson(row)}
          onHandOn={role === "support_worker" ? () => setHandOpen(true) : undefined}
        />
      )}
      {tab === "Person" && (
        <PersonScreen
          profile={profile}
          events={events}
          flags={flags}
          chart={chart}
          patternHit={patternHit}
          showPages={!isFamily}
          onOpenQuote={setQuote}
          onBrief={makeBrief}
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
          onHandoverFamily={() => makeHandover("family")}
          canWriteShift={role === "support_worker"}
          startKind={pageKind}
        />
      )}
    </Shell>
  );
}
