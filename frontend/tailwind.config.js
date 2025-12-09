/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        coffee: {
          50: '#f9f6f3',
          100: '#efe8e1',
          200: '#e0d0c2',
          300: '#cbb09a',
          400: '#b58b6c',
          500: '#a36d4d',
          600: '#8a553b',
          700: '#734331',
          800: '#5e382d',
          900: '#4d2f27',
          950: '#2a1814',
        },
        cream: {
          50: '#fffbf7',
          100: '#fff6ec',
          200: '#ffe9d3',
          300: '#ffd6a8',
          400: '#ffba75',
          500: '#ff9842',
          600: '#f57a1f',
          700: '#cc5a16',
          800: '#a34616',
          900: '#843b17',
        }
      },
      animation: {
        fadeIn: 'fadeIn 0.6s ease-out forwards',
        slideUp: 'slideUp 0.5s ease-out forwards',
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        slideUp: {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        'glow': '0 0 15px rgba(163, 109, 77, 0.3)',
      }
    },
  },
  plugins: [],
}
