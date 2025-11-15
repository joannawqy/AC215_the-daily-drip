/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        coffee: {
          50: '#f7f3ef',
          100: '#ede3d6',
          200: '#d9c0a1',
          300: '#c7a074',
          400: '#b68556',
          500: '#a96f42',
          600: '#8f5832',
          700: '#744527',
          800: '#573320',
          900: '#3a1f16',
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.6s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: 0, transform: 'translateY(10px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
