/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        accent: {
          DEFAULT: '#3D5944',
          hover: '#314839',
          soft: '#EAF0EB',
          softBorder: '#C7D6CB',
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}

