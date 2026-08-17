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

export function formatError(text) {
  const raw = String(text || "").trim();
  if (!raw) return "Something went wrong.";
  try {
    const parsed = JSON.parse(raw);
    const detail = parsed?.detail;
    if (typeof detail === "string" && detail.trim()) return detail.trim();
    if (Array.isArray(detail) && detail.length) {
      const first = detail[0];
      if (typeof first === "string" && first.trim()) return first.trim();
      if (first?.msg) return String(first.msg).trim();
    }
    if (typeof parsed?.message === "string" && parsed.message.trim()) return parsed.message.trim();
  } catch (_err) {
    /* already plain text */
  }
  return raw;
}

export function speakFailMessage(err) {
  const msg = formatError(err?.message || err);
  if (/type the log/i.test(msg)) return msg;
  if (/no names heard/i.test(msg)) return `${msg} Type the log instead.`;
  return `Could not write what you said. ${msg} Type the log instead.`;
}

export async function getJson(path) {
  const res = await fetch(`${API}${withPerson(path)}`, { headers: headers() });
  if (!res.ok) throw new Error(formatError(await res.text()));
  return res.json();
}

export async function patchJson(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "PATCH",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error(formatError(await res.text()));
  return res.json();
}

export async function postJson(path, body) {
  const payload = { ...body };
  if (personId && payload.person_id == null && !path.includes("/corridor")) {
    payload.person_id = personId;
  }
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(formatError(await res.text()));
  return res.json();
}

export async function transcribeAudio(blob) {
  const data = new FormData();
  data.append("file", blob, "clip.webm");
  const res = await fetch(`${API}/transcribe`, {
    method: "POST",
    headers: headers(),
    body: data,
  });
  if (!res.ok) throw new Error(formatError(await res.text()));
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
  params.set("use_heuristic", "false");
  const res = await fetch(`${API}/log/audio?${params.toString()}`, {
    method: "POST",
    headers: headers(),
    body: data,
  });
  if (!res.ok) throw new Error(formatError(await res.text()));
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
