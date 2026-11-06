// Reuse Portal's CommonMark parser; bundle this module for the static demo.
import { micromark } from '../EducAgent-Portal/node_modules/micromark/index.js';

export function render(text) {
  return micromark(text, { allowDangerousHtml: false, allowDangerousProtocol: false })
    // Remote images must not load automatically from model-generated Markdown.
    .replace(/<img\b[^>]*>/g, '[image omitted]')
    .replace(/<a href=/g, '<a target="_blank" rel="noopener noreferrer" href=');
}
