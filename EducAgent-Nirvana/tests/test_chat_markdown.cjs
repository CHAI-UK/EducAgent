const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../demo/markdown.js'), 'utf8'), context);
const render = context.NirvanaMarkdown.render;

test('CommonMark paragraphs, lists, emphasis, code and safe links', () => {
  const html = render('First **point**.\n\nSecond paragraph.\n\n- Age\n- Sex\n\n```python\nx = 1\n```\n\n[Reference](https://example.org)');
  assert.match(html, /<p>First <strong>point<\/strong>\.<\/p>/);
  assert.match(html, /<p>Second paragraph\.<\/p>/);
  assert.match(html, /<ul>\s*<li>Age<\/li>/);
  assert.match(html, /<pre><code class="language-python">x = 1/);
  assert.match(html, /rel="noopener noreferrer" href="https:\/\/example.org"/);
});

test('Model output cannot execute raw HTML, unsafe links or load images', () => {
  const html = render('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n[bad](javascript:alert%281%29)\n\n![tracking](https://example.org/pixel.png)');
  assert.doesNotMatch(html, /<script|<img|href="javascript:/i);
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /\[image omitted\]/);
});
