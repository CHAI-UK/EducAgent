// Storage is an optional preference cache, never a prerequisite for the switch.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");
const html = fs.readFileSync(path.join(__dirname, "..", "..", "index.html"), "utf8");
const css = fs.readFileSync(path.join(__dirname, "..", "..", "styles.css"), "utf8");
const palettes = [":root", ':root[data-theme="dark"]'].map(selector => {
  const block = css.slice(css.indexOf(`${selector} {`)).split("}")[0];
  return Object.fromEntries([...block.matchAll(/--([\w-]+):\s*(#[\da-f]{6});/gi)]
    .map(match => [match[1], match[2]]));
});

test("Learning theme respects saved/system choices and still toggles when storage is blocked", () => {
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(match => match[1]);
  for (const blocked of [false, true]) {
    for (const dark of [false, true]) {
      for (const preference of [null, "light", "dark", "invalid"]) {
        let click;
        const attributes = {};
        const button = {
          setAttribute(name, value) { attributes[name] = value; },
          addEventListener(_event, listener) { click = listener; },
        };
        const colour = {};
        const document = {
          documentElement: {dataset: {}},
          querySelector(selector) { return selector === ".theme-toggle" ? button : colour; },
        };
        const saved = [];
        const localStorage = {
          getItem() { if (blocked) throw new Error("Storage unavailable"); return preference; },
          setItem(_key, value) { if (blocked) throw new Error("Storage unavailable"); saved.push(value); },
        };
        const context = vm.createContext({document, localStorage, matchMedia: () => ({matches: dark})});
        for (const source of scripts) assert.doesNotThrow(() => vm.runInContext(source, context));
        const initiallyDark = !blocked && ["light", "dark"].includes(preference)
          ? preference === "dark" : dark;
        assert.equal(document.documentElement.dataset.theme, initiallyDark ? "dark" : "light");
        assert.equal(colour.content, palettes[Number(initiallyDark)].page);
        assert.equal(attributes["aria-pressed"], String(initiallyDark));
        assert.doesNotThrow(click);
        assert.equal(document.documentElement.dataset.theme, initiallyDark ? "light" : "dark");
        assert.equal(colour.content, palettes[Number(!initiallyDark)].page);
        assert.equal(attributes["aria-pressed"], String(!initiallyDark));
        assert.equal(saved.length, blocked ? 0 : 1);
      }
    }
  }
});

test("EducAgent routes precede external resources in content and navigation", () => {
  assert.deepEqual([...html.matchAll(/<section[^>]+id="([^"]+)"/g)].map(match => match[1]),
    ["educagent", "books", "courses", "practical"]);
  const routes = html.match(/<section class="next-routes"[\s\S]*?<\/section>/)[0];
  assert.deepEqual([...routes.matchAll(/href="([^"]+)"/g)].map(match => match[1]),
    ["/portal/", "/nirvana/"]);
  const navigation = html.match(/<nav[\s\S]*?<\/nav>/)[0];
  assert.deepEqual([...navigation.matchAll(/href="([^"]+)"/g)].map(match => match[1]),
    ["/portal/", "/nirvana/", "#books", "#courses", "#practical"]);
  assert.equal([...html.matchAll(/target="_blank"/g)].length, 14);
});

test("CHAI brand tokens and both themes keep readable text contrast", () => {
  assert.equal(palettes[0].page, "#ffffff");
  assert.equal(palettes[0].ink, "#524c63");
  assert.equal(palettes[0].accent, "#487a7b");
  const luminance = hex => hex.slice(1).match(/../g).map(value => {
    const channel = parseInt(value, 16) / 255;
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  }).reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
  for (const palette of palettes) {
    for (const background of ["page", "surface"]) {
      for (const foreground of ["ink", "ink-strong", "muted", "accent", "accent-strong"]) {
        const values = [luminance(palette[foreground]), luminance(palette[background])].sort((a, b) => b - a);
        assert.ok((values[0] + 0.05) / (values[1] + 0.05) >= 4.5,
          `${foreground} must meet AA against ${background}`);
      }
    }
  }
});
