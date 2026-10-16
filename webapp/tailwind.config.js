/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: 'var(--tg-theme-bg-color, #18222d)',
          secondary: 'var(--tg-theme-secondary-bg-color, #131b24)',
          text: 'var(--tg-theme-text-color, #ffffff)',
          hint: 'var(--tg-theme-hint-color, #708499)',
          link: 'var(--tg-theme-link-color, #6ab2f2)',
          button: 'var(--tg-theme-button-color, #2481cc)',
          buttonText: 'var(--tg-theme-button-text-color, #ffffff)',
        }
      }
    },
  },
  plugins: [],
}
