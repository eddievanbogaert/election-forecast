/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'safe-d':   '#1565C0',
        'likely-d': '#1E88E5',
        'lean-d':   '#64B5F6',
        'tossup':   '#9E9E9E',
        'lean-r':   '#EF9A9A',
        'likely-r': '#E53935',
        'safe-r':   '#B71C1C',
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
