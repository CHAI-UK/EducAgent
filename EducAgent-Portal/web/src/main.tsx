import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Theme } from "@astryxdesign/core";
import "@astryxdesign/core/reset.css";
import "@astryxdesign/core/astryx.css";
import "@astryxdesign/theme-neutral/theme.css";
import "katex/dist/katex.min.css";
import { App } from "./App";
import { educagentTheme } from "./theme-educagent";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Theme theme={educagentTheme} mode="light">
      <App />
    </Theme>
  </StrictMode>,
);
