export const TYPE_LABELS = {
  medication: "Medicines",
  symptom: "Symptom",
  meal: "Meal",
  mood: "Mood",
  sleep: "Sleep",
  incident: "Incident",
  note: "Note",
};

export const SUBTYPE_LABELS = {
  dose_late: "Late medicines",
  dose_missed: "Missed medicines",
  confusion: "Confusion",
  agitation: "Agitation",
  appetite_low: "Low appetite",
  vomiting: "Vomiting",
  eaten: "Eaten",
  mood_low: "Low mood",
  note: "Note",
};

export function eventLabel(type, subtype) {
  return SUBTYPE_LABELS[subtype] || TYPE_LABELS[type] || subtype || type;
}

const FLAG_TITLES = {
  medication: "Late medicines",
  confusion: "Confusion",
  appetite_low: "Low appetite",
  vomiting: "Vomiting",
};

export function flagTitle(subtype) {
  return FLAG_TITLES[subtype] || eventLabel(subtype, subtype);
}

export function sentence(text) {
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function shortWhen(iso) {
  return new Date(iso).toLocaleString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
