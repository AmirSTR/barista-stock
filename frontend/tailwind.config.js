/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        tg: {
          bg: 'var(--tg-theme-bg-color, #fef7e5)',
          secondaryBg: 'var(--tg-theme-secondary-bg-color, #f6eed6)',
          text: 'var(--tg-theme-text-color, #1f2937)',
          hint: 'var(--tg-theme-hint-color, #606c38)',
          link: 'var(--tg-theme-link-color, #606c38)',
          button: 'var(--tg-theme-button-color, #606c38)',
          buttonText: 'var(--tg-theme-button-text-color, #fef7e5)',
          accent: '#606c38',
        },
        brand: {
          50: '#f9fbe7',
          100: '#f0f4c3',
          200: '#e6ee9c',
          300: '#dce775',
          400: '#d4e157',
          500: '#606c38', // User's primary olive green
          600: '#525d30',
          700: '#434c27',
          800: '#353c1e',
          900: '#272b15',
          950: '#181b0d',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'scale(0.98)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
