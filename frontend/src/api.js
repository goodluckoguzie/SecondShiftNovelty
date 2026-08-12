const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function getJson(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function postJson(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function transcribeBlob(blob) {
  const data = new FormData();
  data.append("file", blob, "clip.webm");
  const res = await fetch(`${API}/transcribe`, { method: "POST", body: data });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function pdfUrl(kind) {
  return kind === "handover" ? `${API}/handover/latest.pdf` : `${API}/briefs/latest.pdf`;
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
