# Project Coding Rules — DevPilot Textual TUI

These rules MUST be followed by the LLM at all times when working on this project.
They are derived from real bugs encountered during development. Do not violate them.

---

## Rule 1: Textual TUI — Never Share Dataclass Instances Across Widgets

When you write a lookup function that returns metadata from a dictionary using prefix matching,
you MUST return a unique copy of the dataclass with the actual requested ID set — never the shared template object.

If you return the same shared instance to multiple callers, every widget created from it will have
the same ID and Textual will crash with `DuplicateIds`.

```python
# WRONG — do NOT do this
def get_model_info(model_id):
    for key, info in METADATA.items():
        if key in model_id:
            return info  # shared object — all callers get same id field

# CORRECT — always do this
from dataclasses import replace
def get_model_info(model_id):
    for key, info in METADATA.items():
        if key in model_id:
            return replace(info, id=model_id)  # fresh copy, unique id
```

---

## Rule 2: Textual TUI — Never Call scroll_end() Unconditionally

You must NEVER call `scroll_end()` unconditionally on every event, update, or token.
Doing so hijacks the user's manual scroll position and causes constant jitter during streaming.

Always check if the user is already near the bottom before scrolling:

```python
# WRONG — do NOT do this
self.scroll_end(animate=False)  # called on every event, hijacks user scroll

# CORRECT — always do this
def auto_scroll(self):
    """Smooth animated scroll — for discrete message events only."""
    if self.max_scroll_y - self.scroll_y <= 6:
        self.scroll_end(animate=True, duration=0.3)

def snap_scroll(self):
    """Instant scroll during active streaming — animation fights layout reflows."""
    if self.max_scroll_y - self.scroll_y <= 6:
        self.scroll_end(animate=False)
```

- Use `auto_scroll()` (animated) for discrete events: new message sent/received, streaming starts.
- Use `snap_scroll()` (instant) during active token streaming.
- Always fire scroll via `self.app.call_after_refresh(self.snap_scroll)` so it runs after layout.

---

## Rule 3: Textual TUI — Never Call Markdown.update() on Every Streaming Token

You must NEVER update a `Markdown` widget on every single streamed token.
`Markdown.update()` is async and acquires an internal lock. Calling it at token speed
(20–50×/sec) floods asyncio with `CancelledError` because each call cancels the previous lock waiter.

You MUST debounce: buffer tokens freely, render at most every 80ms.

```python
# WRONG
def append(self, token):
    self._buffer += token
    self.query_one("#body", Markdown).update(self._buffer)  # CancelledError storm

# CORRECT
def append(self, token):
    self._buffer += token
    self._schedule_render()

def _schedule_render(self):
    if self._render_pending:
        return
    self._render_pending = True
    self._render_timer = self.set_timer(0.08, self._flush_render)

def _flush_render(self):
    self._render_pending = False
    self._render_timer = None
    self.query_one("#stream-live", Static).update(self._buffer)
```

---

## Rule 4: Textual TUI — Use Static for Live Streaming, Markdown Only on Finalize

You must NEVER use a `Markdown` widget as the live streaming display during token streaming.
Every `Markdown.update()` triggers a full layout reflow, shifting `max_scroll_y` mid-animation
and causing scroll jitter.

**Two-phase rendering pattern — always follow this:**

- **Streaming phase:** use `Static` widget — instant update, no lock, no layout reflow.
- **Finalize phase:** remove `Static`, mount `Markdown` once with the full complete text.

```python
# compose():
yield Static("", id="stream-live")    # fast live display during streaming
yield Static("▍", id="stream-cursor")

# finalize():
self.query_one("#stream-live", Static).remove()
self.mount(Markdown(full_text, id="stream-body"), before=cursor)
self.query_one("#stream-cursor", Static).display = False
```

---

## Rule 5: npm — Always Audit package.json Before Running npm install

Before running `npm install` on ANY project, you MUST check:

1. Every version string in `package.json` actually exists on npm.
   (`@testing-library/react@^17.0.2` does NOT exist — the real package is `^13.x`.)
2. Every package imported in source files is listed in `package.json`.
3. The `"main"` script entry and all `"scripts"` reference files that actually exist on disk.
4. A bundler (Vite, webpack, CRA) is configured if the project has React/JSX source files.
   React JSX files CANNOT run in Node directly without a bundler.

Fix `package.json` before running `npm install` if any check fails.

---

## Rule 6: Vite — JSX Must Be in .jsx Files, Never .js

You must NEVER put JSX syntax inside a `.js` file in a Vite project.
Vite's `vite:import-analysis` plugin cannot parse JSX in `.js` files.
There is NO valid Vite config that fixes this — `esbuild: { loader: 'jsx', include: /\.js$/ }` is invalid.

The ONLY correct solution: name all JSX-containing files with the `.jsx` extension.

```
✅  App.jsx  Home.jsx  Contact.jsx  main.jsx
❌  App.js   Home.js   Contact.js   index.js   (if they contain JSX)
```

Correct minimal `vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, open: true },
})
```

---

## Rule 7: React Router — Always Use v6 API When Installing react-router-dom@^6

When `react-router-dom` version is `^6` or higher, you MUST use the v6 API.
The v5 API (`Switch`, `<Route component={X} />`) was removed and will crash.

```jsx
// WRONG — v5 API removed in v6
import { Switch, Route } from 'react-router-dom'
<Switch><Route path="/" exact component={Home} /></Switch>
<a href="/about">About</a>

// CORRECT — v6 API
import { Routes, Route, Link } from 'react-router-dom'
<Routes><Route path="/" element={<Home />} /></Routes>
<Link to="/about">About</Link>
```

Other v6 changes: `useHistory()` → `useNavigate()`, `<Redirect>` → `<Navigate>`, no `exact` prop needed.

---

## Rule 8: Vite — Correct Project Structure

`index.html` MUST be at the **project root**, NOT inside `public/`.
`public/` is for static assets only (images, favicon, etc.).

```
project-root/
├── index.html          ← root level, contains <div id="root"> and <script type="module">
├── vite.config.js
├── package.json
├── public/             ← static assets only
└── src/
    ├── main.jsx        ← entry point
    └── App.jsx
```

`index.html` must contain:
```html
<div id="root"></div>
<script type="module" src="/src/main.jsx"></script>
```

---

## Rule 9: Always Cross-Check Every Import Against package.json

Before writing any source file, verify every third-party `import` is in `package.json`.
Never assume a package is pre-installed.

Packages frequently forgotten: `axios`, `react-router-dom`, `lodash`, `moment`, `dayjs`, `react-query`, `zustand`.

If you write `import axios from 'axios'` anywhere, `"axios"` MUST be in `package.json` dependencies.
If it is missing, the dev server will crash at startup even though `npm install` succeeded.
