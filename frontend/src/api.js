const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

let demoRole = "support_worker";
let personId = null;

export function setDemoRole(role) {
  demoRole = role || "support_worker";
}

export function setPersonId(id) {
  personId = id;
}

export function getPersonId() {
  return personId;
}

function withPerson(path) {
  if (!personId) return path;
  const join = path.includes("?") ? "&" : "?";
  return `${path}${join}person_id=${personId}`;
}

function headers(extra = {}) {
  return { "X-Demo-Role": demoRole, ...extra };
}

export async function getJson(path) {
  const res = await fetch(`${API}${withPerson(path)}`, { headers: headers() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function postJson(path, body) {
  const payload = { ...body };
  if (personId && payload.person_id == null) payload.person_id = personId;
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function logAudio(blob, extra = {}) {
  const data = new FormData();
  data.append("file", blob, "clip.webm");
  const params = new URLSearchParams();
  if (personId) params.set("person_id", String(personId));
  if (extra.shift_id) params.set("shift_id", String(extra.shift_id));
  if (extra.logger_id) params.set("logger_id", String(extra.logger_id));
  if (extra.urgent) params.set("urgent", "true");
  const res = await fetch(`${API}/log/audio?${params.toString()}`, {
    method: "POST",
    headers: headers(),
    body: data,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function pdfUrl(kind) {
  const base = kind === "handover" ? "/handover/latest.pdf" : "/briefs/latest.pdf";
  return `${API}${withPerson(base)}`;
}

export function speak(text) {
  if (!window.speechSynthesis || !text) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-GB";
  utterance.rate = 1;
  const voices = window.speechSynthesis.getVoices();
  utterance.voice = voices.find((v) => v.lang === "en-GB") || voices[0];
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}
