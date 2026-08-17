export function Avatar({ name, size = "md" }) {
  const initial = (name || "?").trim().charAt(0).toUpperCase();
  const box = size === "lg" ? "h-14 w-14 text-2xl" : "h-10 w-10 text-lg";
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-accent font-bold text-paper ${box}`}
    >
      {initial}
    </span>
  );
}
