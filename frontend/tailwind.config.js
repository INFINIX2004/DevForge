/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        accent: {
          400: "#22d3ee",
          500: "#06b6d4"
        }
      },
      boxShadow: {
        panel: "0 20px 45px rgba(2, 6, 23, 0.35)"
      }
    }
  },
  plugins: []
};
