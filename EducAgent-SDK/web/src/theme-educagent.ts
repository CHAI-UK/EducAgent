import { defineTheme } from "@astryxdesign/core/theme";
import { neutralTheme } from "@astryxdesign/theme-neutral";

export const educagentTheme = defineTheme({
  name: "educagent",
  extends: neutralTheme,
  color: { accent: "#005348", neutralStyle: "warm", contrast: "high" },
  typography: {
    scale: { base: 16, ratio: 1.2 },
    body: { family: "Figtree", fallbacks: "system-ui, sans-serif" },
    heading: {
      family: "Newsreader",
      fallbacks: "Georgia, serif",
      weight: "normal",
      weights: { 1: "normal", 2: "normal", 3: "semibold" },
    },
    code: { family: "ui-monospace", fallbacks: "monospace" },
  },
  radius: { base: 4, multiplier: 1 },
  motion: {
    fast: 175,
    medium: 410,
    slow: 975,
    ratio: 0.75,
    easing: "cubic-bezier(0.24, 1, 0.4, 1)",
  },
  tokens: {
    "--color-accent": "#005348",
    "--color-on-accent": "#FFFFFF",
    "--color-background-body": "#FFFFFF",
    "--color-background-surface": "#FFFFFF",
    "--color-background-muted": "#FBFAF8",
    "--color-text-primary": "#171717",
    "--color-text-secondary": "#525252",
    // Supporting copy carries instructions and status, so keep it at 14px.
    "--text-supporting-size": "0.875rem",
    "--color-border": "#EDEDED",
    "--focus-outline-color": "#005348",
    "--focus-outline-width": "2px",
    "--focus-outline-offset": "3px",
    "--radius-element": "12px",
    "--radius-container": "16px",
    "--radius-page": "24px",
    "--shadow-low": "0 12px 30px rgb(23 23 23 / 8%)",
  },
  components: {
    button: {
      base: {
        borderRadius: "var(--radius-element)",
        fontWeight: "var(--font-weight-semibold)",
        ":active": { transform: "translateY(1px)" },
      },
    },
    "radio-list-item": {
      base: {
        border: "var(--border-width) solid var(--color-border-emphasized)",
        borderRadius: "var(--radius-element)",
        // 12px keeps each option about 48px tall, so three or four fit on screen.
        padding: "var(--spacing-3)",
        marginBlockEnd: "var(--spacing-2)",
      },
      selected: {
        borderColor: "var(--color-accent)",
        backgroundColor: "var(--color-background-muted)",
      },
    },
  },
});
