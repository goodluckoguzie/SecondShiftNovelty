const TONES = {
  primary: "nhs-btn nhs-btn-primary",
  secondary: "nhs-btn nhs-btn-secondary",
  reverse: "nhs-btn nhs-btn-reverse",
  warning: "nhs-btn nhs-btn-warning",
};

export function Press({ tone = "primary", className = "", children, type = "button", ...props }) {
  return (
    <button type={type} className={`${TONES[tone] || TONES.primary} ${className}`} {...props}>
      {children}
    </button>
  );
}
