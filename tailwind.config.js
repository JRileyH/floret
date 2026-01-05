module.exports = {
  content: [
    "./**/templates/**/*.html",
  ],
  theme: {
    extend: {
      fontFamily: {
        'heading': ['Playwrite England SemiJoined', 'cursive'],
        'body': ['Poiret One', 'sans-serif'],
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
    require("daisyui"),
  ],
  daisyui: {
    themes: [
      {
        floret: {
          "primary": "#5b855b",
          "primary-content": "#d4e8d4",
          "secondary": "#cfe5ff",
          "secondary-content": "#1e3a5f",
          "accent": "#ffd4a3",
          "accent-content": "#7d4e1f",
          "neutral": "#a8b5c4",
          "neutral-content": "#ffffff",
          "base-100": "#fffcf9",
          "base-200": "#faf5f1",
          "base-300": "#f4e8e3",
          "base-content": "#3d3836",
          "info": "#cfe5ff",
          "info-content": "#1e3a5f",
          "success": "#d4e8d4",
          "success-content": "#2d522d",
          "warning": "#ffedc4",
          "warning-content": "#7d5200",
          "error": "#f4bdc4",
          "error-content": "#6b1f26",
          "fontFamily": "Poiret One, sans-serif",
          "--heading-font": "Playwrite England SemiJoined, cursive"
        }
      },
    ],
  },
  safelist: [
    'alert-info',
    'alert-success',
    'alert-warning',
    'alert-error',
  ],
};
