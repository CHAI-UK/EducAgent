# Nirvana

Nirvana helps researchers clarify a question and prepare a Causal Research
Brief. It classifies the task, drafts task-specific fields and proposes edits
for explicit acceptance or rejection. Manual edits invalidate confirmation;
pending proposals are excluded from copied Briefs.

Drafts and chat remain in browser memory. Nirvana does not verify evidence,
execute external tools or automatically import a Brief into another service.
Its research state remains separate from Portal learning progress.

See the [main README](../README.md) for installation, shared ELM settings,
local startup and deployment of all three experiences. The
[operations guide](deploy/README.md) covers backups and Linux services.

## Structure

- `demo/`: browser application and public assets.
- `demo_server.py`: task classification, structured framing and chat API.
- `deploy/`: release builder, container configuration and service launcher.
- `chat-markdown.mjs`: safe Markdown renderer source; its compiled browser
  bundle is `demo/markdown.js`.

Check browser JavaScript with `node --check demo/app.js`.
