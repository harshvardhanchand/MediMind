const appColors = require('./src/theme/colors.ts').colors; // Import our colors

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./App.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ...appColors, // Spread our app-specific colors
        // You can also define Tailwind-specific color names here if needed
        // e.g., 'primary-hover': appColors.primaryDark,
      },
    },
  },
  plugins: [],
} 