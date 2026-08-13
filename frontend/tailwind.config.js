import { theme } from "./src/theme.js";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: theme.color.ink,
        muted: theme.color.muted,
        accent: theme.color.accent,
        "dark-blue": theme.color.darkBlue,
        soft: theme.color.soft,
        paper: theme.color.paper,
        danger: theme.color.danger,
        "danger-soft": theme.color.dangerSoft,
        warning: theme.color.warning,
        "warning-soft": theme.color.warningSoft,
        success: theme.color.success,
        "success-soft": theme.color.successSoft,
        line: theme.color.line,
        input: theme.color.input,
        focus: theme.color.focus,
        button: theme.color.button,
        "button-shade": theme.color.buttonShade,
      },
      fontFamily: {
        sans: ["Arial", "Helvetica", "sans-serif"],
      },
      borderRadius: {
        sm: `${theme.radius.sm}px`,
        md: `${theme.radius.md}px`,
      },
      minHeight: {
        press: "48px",
        speak: "56px",
      },
    },
  },
  plugins: [],
};
