/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/App.{js,jsx,ts,tsx}",
    "./frontend/src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        // Core Apple Health Inspired Colors
        'background-primary': '#F9F9F9',
        'background-secondary': '#FFFFFF',
        'background-tertiary': '#EFEFF4',
        'text-primary': '#000000',
        'text-secondary': '#8A8A8E',
        'text-muted': '#AEAEB2',
        'accent-primary': '#007AFF',
        'accent-primary-pressed': '#0056B3',
        'accent-destructive': '#FF3B30',
        'border-subtle': '#E5E5EA',
        'border-strong': '#D1D1D6',
        
        // Semantic colors
        success: '#34C759',
        warning: '#FF9500',
        error: '#FF3B30',
        info: '#007AFF',
        
        // Data visualization colors
        'data-1': '#5AC8FA',
        'data-2': '#34C759',
        'data-3': '#FF9500',
        'data-4': '#FF2D55',
        'data-5': '#AF52DE',
        'data-6': '#FF6B2D',
        'data-7': '#00C7BE',
        'data-8': '#5856D6',
      },
    },
  },
  plugins: [],
} 