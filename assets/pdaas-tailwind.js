tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        win: {
          50: '#e6f2ff', 100: '#cce5ff', 200: '#99ccff', 300: '#66b3ff',
          400: '#4cc2ff', 500: '#0067c0', 600: '#005fb8', 700: '#00458c',
          base: '#202020', dark: '#1c1c1c', card: '#272727',
          hover: '#2d2d2d', active: '#333333', border: '#383838',
        }
      }
    }
  }
};