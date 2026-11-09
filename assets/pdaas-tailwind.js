tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Segoe UI Variable Text"', '"Segoe UI"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        win: {
          50: '#e6f2ff', 100: '#cce5ff', 200: '#99ccff', 300: '#66b3ff',
          400: '#77caff', 500: '#1769aa', 600: '#12558e', 700: '#0c416e',
          base: '#191c22', dark: '#14171c', card: '#242830',
          hover: '#2c313b', active: '#363d49', border: '#393f4b',
        }
      }
    }
  }
};
