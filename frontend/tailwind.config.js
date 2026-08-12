/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1a2332",
        muted: "#5a6577",
        accent: "#1e5f8a",
        soft: "#f4f7fb",
      },
    },
  },
  plugins: [],
};
