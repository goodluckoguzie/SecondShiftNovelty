export const TYPE_LABELS = {
  medication: "Medicines",
  symptom: "Symptom",
  meal: "Meal",
  mood: "Mood",
  sleep: "Sleep",
  incident: "Incident",
  preference: "About them",
  note: "Note",
  from_home: "From home",
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
  not_himself: "Not himself",
  awake_night: "Up in the night",
  settled_late: "Settled late",
  fall: "Fall",
  about_me: "About them",
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
  hospital_return: "Back from hospital",
  not_himself: "Not himself",
};

export function flagTitle(subtype) {
  return FLAG_TITLES[subtype] || eventLabel(subtype, subtype);
}

export function sentence(text) {
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function joinCopy(...parts) {
  return parts
    .filter((part) => part != null && String(part).trim() !== "")
    .map(String)
    .join(", ");
}

export function shortWhen(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function clock(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export function cardWhen(iso) {
  if (!iso) return "";
  const at = new Date(iso);
  const now = new Date();
  const sameDay =
    at.getFullYear() === now.getFullYear() && at.getMonth() === now.getMonth() && at.getDate() === now.getDate();
  if (sameDay) return clock(iso);
  return at.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export function eventFacts(event) {
  const slots = event?.slots || {};
  const parts = [];
  if (event?.event_time) parts.push(clock(event.event_time));
  if (slots.meal) parts.push(slots.meal);
  if (slots.food) parts.push(slots.food);
  if (slots.amount) parts.push(slots.amount);
  if (slots.place) parts.push(slots.place);
  if (slots.sequence === "after_meal") parts.push("after the meal");
  if (slots.minutes_late) parts.push(`${slots.minutes_late} minutes late`);
  return parts.join(" · ");
}

export function voiceLabel(event) {
  if (!event) return "";
  if ((event.source || "staff") === "from_home" || String(event.logger_label || "").includes("(home)")) {
    return "Home";
  }
  return "Wing";
}

export function wingFlagLine(row) {
  const flag = (row?.flags || [])[0];
  if (!flag) return "";
  if (flag.subtype === "vomiting") return "Vomited after meals last week. Still open.";
  if (flag.subtype === "confusion") return "Confusion more than once this week.";
  if (flag.subtype === "medication") return "Late or missed tablets this week.";
  if (flag.subtype === "hospital_return") return "Back from hospital.";
  if (flag.subtype === "not_himself") return "Not himself this week.";
  if (flag.subtype === "appetite_low") return "Low appetite this week.";
  return flag.message || "";
}

export function wingCarryLine(row) {
  const flag = (row?.flags || [])[0];
  if (!flag) return "";
  if (flag.subtype === "vomiting") return "sick after meals";
  if (flag.subtype === "confusion") return "confusion this week";
  if (flag.subtype === "medication") return "late tablets";
  if (flag.subtype === "hospital_return") return "back from hospital";
  if (flag.subtype === "not_himself") return "not himself";
  if (flag.subtype === "appetite_low") return "low appetite";
  return String(flag.message || "").split(".")[0].toLowerCase();
}

export function wingCardLine(row) {
  const carry = wingCarryLine(row);
  if (carry) return carry;
  const when = cardWhen(row?.when || row?.last_at);
  const label = eventLabel(row?.last_type, row?.last_subtype);
  if (label) {
    const short = label.toLowerCase();
    return when ? `${short} · ${when}` : short;
  }
  const raw = String(row?.line || "")
    .split(/[.!?]/)[0]
    .trim();
  if (raw) {
    const clipped = raw.length > 36 ? `${raw.slice(0, 33)}…` : raw;
    return when ? `${clipped} · ${when}` : clipped;
  }
  return "nothing repeating";
}

export function extractPattern(result, fallbackName) {
  if (!result || result.emergency) return null;
  const slices = result.slices || [];
  const candidates = slices.length ? slices : [result];
  for (const payload of candidates) {
    const similar = payload.similar || [];
    const flags = payload.flags || [];
    const flag =
      flags.find((item) =>
        ["vomiting", "confusion", "not_himself", "hospital_return", "medication", "appetite_low"].includes(
          item.subtype,
        ),
      ) || flags[0];
    const today = (payload.events || []).find((event) => event.subtype && event.subtype !== "note" && event.subtype !== "eaten") || (payload.events || [])[0];
    const last =
      (today && similar.find((event) => event.subtype === today.subtype)) || similar[0] || (flag?.evidence || [])[0];
    if (!flag && !last) continue;
    return {
      personId: payload.person_id,
      personName: payload.person_name || fallbackName || "",
      confirmation: payload.confirmation || result.confirmation || "",
      flag,
      today,
      similar: similar.slice(0, 3),
      last,
    };
  }
  return null;
}
