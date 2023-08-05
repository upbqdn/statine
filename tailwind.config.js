module.exports = {
  content: ["./layouts/*/*.{html,js}"],
  theme: {
    container: {
      center: true,
      screens: {
        sm: "40rem",
        md: "40rem",
        lg: "40rem",
        xl: "40rem",
        "2xl": "40rem",
      },
    },
    extend: {
      lineHeight: {
        loose: "1.9",
      },
      colors: {
        "tp-black": "rgba(0,0,0,.8)",
        dark: "#1d1f21",
      },
      fontFamily: {
        sans: [
          "ComputerModernSerif",
          "BlinkMacSystemFont",
          "avenir next",
          "avenir",
          "segoe ui",
          "helvetica neue",
          "helvetica",
          "Cantarell",
          "Ubuntu",
          "roboto",
          "noto",
          "arial",
          "sans-serif",
        ],
      },
      gridTemplateColumns: {
        nav: "repeat(auto-fill, minmax(80px, 1fr))",
        "minimal-list-item": "15% 85%",
        "list-item": ".6fr 3fr auto 1fr",
      },
    },
  },
  plugins: [],
  darkMode: "class",
};
