import { personPhoto } from "../people.js";

export function Avatar({ name, size = "md" }) {
  const photo = personPhoto(name);
  const box = size === "lg" ? "h-14 w-14 text-2xl" : size === "tile" ? "h-full w-full text-2xl" : "h-10 w-10 text-lg";
  const rounded = size === "tile" ? "rounded-sm" : "rounded-full";
  if (photo) {
    return (
      <img
        src={photo}
        alt=""
        className={`inline-block shrink-0 object-cover ${box} ${rounded}`}
      />
    );
  }
  const initial = (name || "?").trim().charAt(0).toUpperCase();
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center bg-accent font-bold text-paper ${box} ${rounded}`}
    >
      {initial}
    </span>
  );
}
