/**
 * AgentVerse Web IDE — app.js
 * ============================================================
 * Sections:
 *  1. CONFIG & STATE
 *  2. WEBSOCKET
 *  3. PIPELINE BAR
 *  4. FILE TREE
 *  5. MONACO EDITOR
 *  6. AGENT CARDS
 *  7. TELEMETRY
 *  8. FILE ACTIVITY
 *  9. BOTTOM PANEL (Logs, Terminal, Chat, Tests, Git)
 * 10. TOAST NOTIFICATIONS
 * 11. EVENT ROUTING
 * 12. INIT
 */

"use strict";

// ══════════════════════════════════════════════════════════════
// 1. CONFIG & STATE
// ══════════════════════════════════════════════════════════════
const WS_URL = `ws://${location.host}/ws`;

const PIPELINE_STAGES = [
  { id: "prompt",    label: "Prompt",        icon: "💬" },
  { id: "planning",  label: "Planning",       icon: "🧭" },
  { id: "architect", label: "Architecture",   icon: "🏗" },
  { id: "coding",    label: "Coding",         icon: "💻" },
  { id: "validate",  label: "Validation",     icon: "✅" },
  { id: "testing",   label: "Testing",        icon: "🧪" },
  { id: "review",    label: "Review",         icon: "👀" },
  { id: "docs",      label: "Docs",           icon: "📝" },
  { id: "git",       label: "Git Commit",     icon: "🌿" },
  { id: "done",      label: "Completed",      icon: "🎉" },
];

const AGENTS = [
  { id: "planner",       name: "Planner",       icon: "🧭", desc: "Breaking goal into tasks" },
  { id: "architect",     name: "Architect",     icon: "🏗",  desc: "Designing folder & stack" },
  { id: "coder",         name: "Coder",         icon: "💻", desc: "Generating source files" },
  { id: "validator",     name: "Validator",     icon: "✅", desc: "Validating code & standards" },
  { id: "tester",        name: "Tester",        icon: "🧪", desc: "Writing test coverage" },
  { id: "reviewer",      name: "Reviewer",      icon: "👀", desc: "Reviewing before commit" },
  { id: "documentation", name: "Documentation", icon: "📝", desc: "Generating README & docs" },
  { id: "github",        name: "GitHub",        icon: "🌿", desc: "Managing Git & PRs" },
];

const FILE_ICONS = {
  py: "🐍", js: "📜", jsx: "⚛️", ts: "📘", tsx: "⚛️",
  html: "🌐", css: "🎨", json: "⚙️", yaml: "⚙️", yml: "⚙️",
  md: "📝", sh: "⚡", bash: "⚡", toml: "🔧", env: "🔒",
  png: "🖼️", jpg: "🖼️", svg: "🖼️", gif: "🖼️",
  zip: "📦", gz: "📦", rs: "🦀", go: "🐹", java: "☕",
  cpp: "⚙️", c: "⚙️", rb: "💎", lock: "🔒",
};
const DIR_ICONS = { open: "▾", closed: "▸" };

const state = {
  ws: null,
  wsReady: false,
  reconnectTimer: null,

  openFiles: {},      // path → { content, language, modified }
  activeFile: null,
  activePath: null,

  agentTimers: {},     // agentId → interval id
  chatBuffer: "",
  activeChatMsg: null,

  currentPipelineStage: null,
  completedStages: new Set(),
};

// ══════════════════════════════════════════════════════════════
// 2. WEBSOCKET
// ══════════════════════════════════════════════════════════════
function connectWS() {
  if (state.ws) {
    try { state.ws.close(); } catch (_) {}
  }

  const ws = new WebSocket(WS_URL);
  state.ws = ws;

  ws.onopen = () => {
    state.wsReady = true;
    clearTimeout(state.reconnectTimer);
    setConnStatus(true);
    addLog("Connected to AgentVerse backend", "success");
  };

  ws.onmessage = (evt) => {
    try {
      const msg = JSON.parse(evt.data);
      routeEvent(msg);
    } catch (e) { /* ignore */ }
  };

  ws.onerror = () => {
    state.wsReady = false;
    setConnStatus(false);
  };

  ws.onclose = () => {
    state.wsReady = false;
    setConnStatus(false);
    state.reconnectTimer = setTimeout(connectWS, 3000);
    addLog("Disconnected — reconnecting in 3s…", "warn");
  };
}

function wsSend(data) {
  if (state.wsReady && state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify(data));
  }
}

// ══════════════════════════════════════════════════════════════
// 3. PIPELINE BAR
// ══════════════════════════════════════════════════════════════
function buildPipelineBar() {
  const bar = document.getElementById("pipeline-bar");
  bar.innerHTML = "";
  PIPELINE_STAGES.forEach((stage, idx) => {
    const pill = document.createElement("div");
    pill.className = "pipeline-stage";
    pill.innerHTML = `
      <div class="stage-pill" id="stage-${stage.id}" title="${stage.label}">
        <span class="stage-num">${idx + 1}</span>
        <span class="stage-icon">${stage.icon}</span>
        <span class="stage-label">${stage.label}</span>
      </div>`;
    bar.appendChild(pill);

    if (idx < PIPELINE_STAGES.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = "stage-arrow";
      arrow.textContent = "›";
      bar.appendChild(arrow);
    }
  });
  // Set initial state
  setPipelineStage("prompt");
}

function setPipelineStage(stageId) {
  const normalized = stageId.toLowerCase().replace(/\s+/g, "");
  let matched = null;
  for (const s of PIPELINE_STAGES) {
    if (s.id === normalized || s.label.toLowerCase().replace(/\s+/g, "") === normalized ||
        normalized.includes(s.id) || s.id.includes(normalized.slice(0, 5))) {
      matched = s.id;
      break;
    }
  }
  if (!matched) return;

  state.currentPipelineStage = matched;

  PIPELINE_STAGES.forEach(s => {
    const el = document.getElementById(`stage-${s.id}`);
    if (!el) return;
    el.classList.remove("active", "done");
    if (state.completedStages.has(s.id)) {
      el.classList.add("done");
      el.querySelector(".stage-num").textContent = "✓";
    } else if (s.id === matched) {
      el.classList.add("active");
    }
  });

  // Scroll active stage into view
  const activeEl = document.getElementById(`stage-${matched}`);
  if (activeEl) activeEl.scrollIntoView({ inline: "center", behavior: "smooth" });
}

function completePipelineStage(stageId) {
  const normalized = stageId.toLowerCase();
  for (const s of PIPELINE_STAGES) {
    if (s.id === normalized || s.label.toLowerCase().includes(normalized)) {
      state.completedStages.add(s.id);
      const el = document.getElementById(`stage-${s.id}`);
      if (el) {
        el.classList.remove("active");
        el.classList.add("done");
        el.querySelector(".stage-num").textContent = "✓";
      }
      break;
    }
  }
}

// ══════════════════════════════════════════════════════════════
// 4. FILE TREE
// ══════════════════════════════════════════════════════════════
function renderTree(node, container, depth = 0) {
  if (!node || !node.name) return;

  const item = document.createElement("div");
  item.className = "tree-item";
  item.dataset.path = node.path;
  item.dataset.type = node.type;

  const indent = depth > 0 ? `<span class="tree-indent" style="width:${depth * 12}px"></span>` : "";

  if (node.type === "dir") {
    const icon = DIR_ICONS.closed;
    item.innerHTML = `
      ${indent}
      <span class="tree-toggle">${icon}</span>
      <span class="tree-icon">📁</span>
      <span class="tree-name">${escHtml(node.name)}</span>`;
    item.addEventListener("click", () => toggleDir(item, node, depth));
  } else {
    const ext = node.name.split(".").pop().toLowerCase();
    const icon = FILE_ICONS[ext] || "📄";
    item.innerHTML = `
      ${indent}
      <span class="tree-toggle"></span>
      <span class="tree-icon">${icon}</span>
      <span class="tree-name">${escHtml(node.name)}</span>`;
    item.addEventListener("click", () => openFileFromTree(node.path, item));
  }

  container.appendChild(item);
}

function toggleDir(item, node, depth) {
  const isOpen = item.dataset.open === "1";
  const toggle = item.querySelector(".tree-toggle");
  const icon   = item.querySelector(".tree-icon");

  if (isOpen) {
    // Collapse
    item.dataset.open = "0";
    toggle.textContent = DIR_ICONS.closed;
    icon.textContent = "📁";
    const children = item.nextElementSibling;
    if (children && children.dataset.treeChildren) children.remove();
  } else {
    // Expand
    item.dataset.open = "1";
    toggle.textContent = DIR_ICONS.open;
    icon.textContent = "📂";
    if (node.children && node.children.length > 0) {
      const childContainer = document.createElement("div");
      childContainer.dataset.treeChildren = "1";
      node.children.forEach(child => renderTree(child, childContainer, depth + 1));
      item.insertAdjacentElement("afterend", childContainer);
    }
  }
}

function renderFileTree(tree) {
  const container = document.getElementById("file-tree");
  container.innerHTML = "";
  if (tree && tree.children) {
    tree.children.forEach(child => renderTree(child, container, 0));
  }
}

function openFileFromTree(path, treeItem) {
  // Deactivate old
  document.querySelectorAll(".tree-item.active").forEach(el => el.classList.remove("active"));
  if (treeItem) treeItem.classList.add("active");
  wsSend({ type: "read_file", path });
}

function highlightFileInTree(path, state = "glowing") {
  const item = document.querySelector(`.tree-item[data-path="${CSS.escape(path)}"]`);
  if (item) {
    item.classList.remove("glowing", "saved", "new-file");
    item.classList.add(state);
  }
}

function addFileToTree(path) {
  const existing = document.querySelector(`.tree-item[data-path="${CSS.escape(path)}"]`);
  if (existing) { highlightFileInTree(path, "glowing"); return; }

  const parts = path.split(/[\\/]/);
  const name = parts[parts.length - 1];
  const ext = name.split(".").pop().toLowerCase();
  const icon = FILE_ICONS[ext] || "📄";

  const item = document.createElement("div");
  item.className = "tree-item new-file";
  item.dataset.path = path;
  item.dataset.type = "file";
  item.innerHTML = `<span class="tree-icon">${icon}</span><span class="tree-name">${escHtml(name)}</span>`;
  item.addEventListener("click", () => openFileFromTree(path, item));

  document.getElementById("file-tree").prepend(item);
}

// ══════════════════════════════════════════════════════════════
// 5. MONACO EDITOR
// ══════════════════════════════════════════════════════════════
let monacoEditor = null;
let liveTyper    = null;

function initMonaco() {
  require.config({
    paths: { vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs" }
  });

  require(["vs/editor/editor.main"], function () {
    // AgentVerse Dark Theme — GitHub token colors
    monaco.editor.defineTheme("agentverse-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "comment",       foreground: "7D8590", fontStyle: "italic" },
        { token: "keyword",       foreground: "FF7B72" },
        { token: "keyword.flow",  foreground: "FF7B72" },
        { token: "string",        foreground: "A5D6FF" },
        { token: "string.escape", foreground: "79C0FF" },
        { token: "number",        foreground: "79C0FF" },
        { token: "type",          foreground: "FFA657" },
        { token: "class",         foreground: "F0883E" },
        { token: "function",      foreground: "D2A8FF" },
        { token: "variable",      foreground: "E6EDF3" },
        { token: "decorator",     foreground: "2EA043" },
        { token: "regexp",        foreground: "A5D6FF" },
      ],
      colors: {
        "editor.background":                "#0D1117",
        "editor.foreground":                "#E6EDF3",
        "editor.lineHighlightBackground":   "#161B22",
        "editor.selectionBackground":       "#1C3A5E",
        "editor.inactiveSelectionBackground": "#1C3A5E80",
        "editorLineNumber.foreground":      "#484F58",
        "editorLineNumber.activeForeground":"#7D8590",
        "editorCursor.foreground":          "#2F81F7",
        "editorWidget.background":          "#161B22",
        "editorWidget.border":              "#30363D",
        "editorSuggestWidget.background":   "#1C2128",
        "editorSuggestWidget.selectedBackground": "#2D333B",
        "input.background":                 "#0D1117",
        "input.border":                     "#30363D",
        "minimap.background":               "#0D1117",
        "scrollbar.shadow":                 "#010409",
        "scrollbarSlider.background":       "#30363D80",
        "scrollbarSlider.hoverBackground":  "#30363D",
        "scrollbarSlider.activeBackground": "#2F81F7",
        "editorBracketMatch.background":    "#17E5E650",
        "editorBracketMatch.border":        "#17E5E6",
      },
    });

    monacoEditor = monaco.editor.create(
      document.getElementById("monaco-container"),
      {
        value: [
          "// ◈  AgentVerse Web IDE",
          "// ─────────────────────────────────────────────────────",
          "// Describe what you want to build in the Chat panel ↓",
          "// The AI pipeline will generate your full project here.",
          "//",
          "// Planner  → Architect → Coder → Validator",
          "// Tester   → Reviewer  → Docs  → Git Commit",
        ].join("\n"),
        language: "javascript",
        theme: "agentverse-dark",
        automaticLayout: true,
        fontSize: 13.5,
        fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
        fontLigatures: true,
        lineNumbers: "on",
        minimap: { enabled: true, scale: 1, renderCharacters: false },
        scrollBeyondLastLine: false,
        wordWrap: "off",
        renderLineHighlight: "all",
        cursorBlinking: "smooth",
        cursorSmoothCaretAnimation: "on",
        smoothScrolling: true,
        padding: { top: 12, bottom: 20 },
        bracketPairColorization: { enabled: true },
        guides: {
          bracketPairs: "active",
          indentation: true,
        },
        suggest: { insertMode: "replace" },
        overviewRulerBorder: false,
        renderWhitespace: "none",
        formatOnPaste: true,
        tabSize: 2,
      }
    );

    liveTyper = new LiveTyper(monacoEditor);

    // Update status bar on cursor change
    monacoEditor.onDidChangeCursorPosition((e) => {
      const pos = e.position;
      document.getElementById("editor-ln-col").textContent =
        `Ln ${pos.lineNumber}, Col ${pos.column}`;
    });

    // Load initial file tree
    wsSend({ type: "get_files" });
  });
}

function openFileInEditor(path, content, language) {
  if (!monacoEditor) return;
  state.activePath = path;

  // Update tabs
  addEditorTab(path, content, language);

  // Set content
  const model = monacoEditor.getModel();
  if (model) {
    const old = monaco.editor.createModel(content, language);
    monacoEditor.setModel(old);
  }

  // Update breadcrumbs
  setBreadcrumbs(path);

  // Update status bar
  document.getElementById("editor-language").textContent =
    (language || "plaintext").toUpperCase();
}

function liveTypeContent(path, content, language) {
  if (!monacoEditor || !liveTyper) return;

  state.activePath = path;
  addEditorTab(path, "", language);
  setBreadcrumbs(path);

  const model = monaco.editor.createModel("", language || "plaintext");
  monacoEditor.setModel(model);

  document.getElementById("editor-language").textContent =
    (language || "plaintext").toUpperCase();

  const indicator = document.getElementById("typing-indicator");
  indicator.classList.add("visible");

  liveTyper.type(content, () => {
    indicator.classList.remove("visible");
    highlightFileInTree(path, "saved");
    showToast(`✓ Wrote ${path.split(/[\\/]/).pop()}`, "success");
  });
}

// Live Typer
class LiveTyper {
  constructor(editor) {
    this.editor = editor;
    this.queue  = [];
    this.running = false;
    this.BATCH  = 4;   // chars per tick
    this.TICK   = 18;  // ms per tick
    this.onDone = null;
  }

  type(text, onDone) {
    this.queue  = text.split("");
    this.onDone = onDone || null;
    if (!this.running) this._tick();
  }

  _tick() {
    if (!this.queue.length) {
      this.running = false;
      if (this.onDone) this.onDone();
      return;
    }
    this.running = true;
    const chars = this.queue.splice(0, this.BATCH).join("");
    const model = this.editor.getModel();
    if (!model) { this.running = false; return; }
    const len = model.getValueLength();
    const pos = model.getPositionAt(len);
    this.editor.executeEdits("live-type", [{
      range: new monaco.Range(pos.lineNumber, pos.column, pos.lineNumber, pos.column),
      text: chars,
    }]);
    this.editor.revealLine(model.getLineCount(), monaco.editor.ScrollType.Smooth);
    setTimeout(() => this._tick(), this.TICK);
  }

  abort() {
    this.queue   = [];
    this.running = false;
  }
}

// Editor tabs
const openTabs = {};
function addEditorTab(path, content, language) {
  const name = path.split(/[\\/]/).pop();
  const ext  = name.split(".").pop().toLowerCase();
  const icon = FILE_ICONS[ext] || "📄";

  openTabs[path] = { content, language };

  const tabBar = document.getElementById("editor-tabs");
  let tab = tabBar.querySelector(`[data-tab-path="${CSS.escape(path)}"]`);
  if (!tab) {
    tab = document.createElement("div");
    tab.className = "editor-tab";
    tab.dataset.tabPath = path;
    tab.innerHTML = `
      <span class="tab-icon">${icon}</span>
      <span>${escHtml(name)}</span>
      <span class="tab-close" title="Close">✕</span>`;
    tab.addEventListener("click", (e) => {
      if (e.target.classList.contains("tab-close")) {
        closeTab(path, tab);
      } else {
        switchToTab(path);
      }
    });
    tabBar.appendChild(tab);
  }
  switchToTab(path);
}

function switchToTab(path) {
  document.querySelectorAll(".editor-tab").forEach(t => t.classList.remove("active"));
  const tab = document.querySelector(`[data-tab-path="${CSS.escape(path)}"]`);
  if (tab) tab.classList.add("active");
  state.activePath = path;
  setBreadcrumbs(path);
}

function closeTab(path, tabEl) {
  delete openTabs[path];
  tabEl.remove();
  // If no tabs left, clear editor
  if (!document.querySelectorAll(".editor-tab").length) {
    monacoEditor?.getModel()?.setValue("// No file open");
    document.getElementById("editor-breadcrumbs").innerHTML = "";
  }
}

function setBreadcrumbs(path) {
  const parts = path.replace(/\\/g, "/").split("/");
  const crumbs = document.getElementById("editor-breadcrumbs");
  crumbs.innerHTML = parts
    .map((p, i) =>
      `<span class="breadcrumb-item ${i === parts.length - 1 ? "active" : ""}">${escHtml(p)}</span>`)
    .join('<span class="breadcrumb-sep">›</span>');
}

// ══════════════════════════════════════════════════════════════
// 6. AGENT CARDS
// ══════════════════════════════════════════════════════════════
function buildAgentCards() {
  const container = document.getElementById("agent-cards");
  container.innerHTML = "";
  AGENTS.forEach(agent => {
    const card = document.createElement("div");
    card.className = "agent-card waiting";
    card.id = `agent-card-${agent.id}`;
    card.innerHTML = `
      <div class="agent-card-header">
        <span class="agent-icon">${agent.icon}</span>
        <span class="agent-name">${agent.name}</span>
        <span class="agent-status-icon" id="agi-${agent.id}">○</span>
      </div>
      <div class="agent-task" id="agt-${agent.id}">${agent.desc}</div>
      <div class="agent-progress-bar">
        <div class="agent-progress-fill" id="agp-${agent.id}"></div>
      </div>
      <div class="agent-meta">
        <span id="agpct-${agent.id}">0%</span>
        <span id="agtim-${agent.id}">—</span>
      </div>`;
    container.appendChild(card);
  });
}

function setAgentStatus(rawName, status, task) {
  const id = resolveAgentId(rawName);
  if (!id) return;

  const card   = document.getElementById(`agent-card-${id}`);
  const icon   = document.getElementById(`agi-${id}`);
  const taskEl = document.getElementById(`agt-${id}`);
  const fill   = document.getElementById(`agp-${id}`);
  const pct    = document.getElementById(`agpct-${id}`);
  const tim    = document.getElementById(`agtim-${id}`);
  if (!card) return;

  card.className = `agent-card ${status}`;

  if (status === "running") {
    icon.textContent = "⠋";
    icon.style.color = "#2F81F7";
    startAgentSpinner(id);
    startAgentTimer(id, tim);
    fill.style.width = "30%";
    pct.textContent = "30%";
    if (task) taskEl.textContent = task.slice(0, 50);
  } else if (status === "done") {
    icon.textContent = "✓";
    icon.style.color = "#56D364";
    stopAgentSpinner(id);
    stopAgentTimer(id);
    fill.style.width = "100%";
    pct.textContent = "100%";
  } else if (status === "failed") {
    icon.textContent = "✗";
    icon.style.color = "#F85149";
    stopAgentSpinner(id);
    stopAgentTimer(id);
  } else {
    icon.textContent = "○";
    icon.style.color = "#7D8590";
    stopAgentSpinner(id);
    stopAgentTimer(id);
    fill.style.width = "0%";
    pct.textContent = "0%";
  }
}

const BRAILLE_FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"];
const spinnerTimers = {};

function startAgentSpinner(id) {
  stopAgentSpinner(id);
  let idx = 0;
  spinnerTimers[id] = setInterval(() => {
    const icon = document.getElementById(`agi-${id}`);
    if (icon) icon.textContent = BRAILLE_FRAMES[idx++ % BRAILLE_FRAMES.length];
  }, 100);
}

function stopAgentSpinner(id) {
  if (spinnerTimers[id]) {
    clearInterval(spinnerTimers[id]);
    delete spinnerTimers[id];
  }
}

const agentClocks = {};
function startAgentTimer(id, el) {
  stopAgentTimer(id);
  const start = Date.now();
  agentClocks[id] = setInterval(() => {
    const elapsed = Math.floor((Date.now() - start) / 1000);
    const m = String(Math.floor(elapsed / 60)).padStart(2, "0");
    const s = String(elapsed % 60).padStart(2, "0");
    if (el) el.textContent = `${m}:${s}`;
  }, 1000);
}

function stopAgentTimer(id) {
  if (agentClocks[id]) {
    clearInterval(agentClocks[id]);
    delete agentClocks[id];
  }
}

function resolveAgentId(rawName) {
  if (!rawName) return null;
  const lower = rawName.toLowerCase().replace(/agent$/, "").trim();
  for (const a of AGENTS) {
    if (a.id === lower || a.name.toLowerCase() === lower || a.id.includes(lower) || lower.includes(a.id)) {
      return a.id;
    }
  }
  return null;
}

function updateAgentProgress(agentName, pct) {
  const id = resolveAgentId(agentName);
  if (!id) return;
  const fill = document.getElementById(`agp-${id}`);
  const pctEl = document.getElementById(`agpct-${id}`);
  if (fill) fill.style.width = `${pct}%`;
  if (pctEl) pctEl.textContent = `${pct}%`;
}

// ══════════════════════════════════════════════════════════════
// 7. TELEMETRY
// ══════════════════════════════════════════════════════════════
const telemetry = { tokens: 0, files: 0, loc: 0, tests: 0 };

function updateTelemetryUI() {
  setTeleValue("tele-tokens", fmtNum(telemetry.tokens), "purple");
  setTeleValue("tele-files",  String(telemetry.files),  "blue");
  setTeleValue("tele-loc",    fmtNum(telemetry.loc),    "green");
  setTeleValue("tele-tests",  String(telemetry.tests),  "amber");
}

function setTeleValue(id, value, colorClass) {
  const el = document.getElementById(id);
  if (el) { el.textContent = value; el.className = `tele-value ${colorClass}`; }
}

function fmtNum(n) {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

// ══════════════════════════════════════════════════════════════
// 8. FILE ACTIVITY
// ══════════════════════════════════════════════════════════════
const seenActivities = new Set();

function addFileActivity(path, op) {
  const key = `${op}:${path}`;
  if (seenActivities.has(key)) return;
  seenActivities.add(key);

  const name = path.split(/[\\/]/).pop();
  const list = document.getElementById("file-activity-list");

  let icon, color;
  if (op === "create" || op === "creating") { icon = "+"; color = "#56D364"; }
  else if (op === "edit" || op === "editing") { icon = "✏"; color = "#E3B341"; }
  else if (op === "read") { icon = "📖"; color = "#7D8590"; }
  else { icon = "🗑"; color = "#F85149"; }

  const row = document.createElement("div");
  row.className = "file-activity-row";
  row.id = `fa-${key.replace(/[^a-z0-9]/gi, "_")}`;
  row.innerHTML = `
    <span class="fa-icon" style="color:${color}">${icon}</span>
    <span class="fa-name" title="${escHtml(path)}">${escHtml(name)}</span>
    <span class="fa-status" id="fas-${row.id}">⠋</span>`;
  list.prepend(row);

  // Keep max 8 items
  while (list.children.length > 8) list.lastElementChild.remove();
}

function finishFileActivity(path, op) {
  const key = `${op}:${path}`;
  const safeId = `fa-${key.replace(/[^a-z0-9]/gi, "_")}`;
  const statusEl = document.getElementById(`fas-${safeId}`);
  if (statusEl) { statusEl.textContent = "✓"; statusEl.classList.add("done"); }
}

// ══════════════════════════════════════════════════════════════
// 9. BOTTOM PANEL
// ══════════════════════════════════════════════════════════════
function initBottomTabs() {
  document.querySelectorAll(".bottom-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".bottom-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".bottom-pane").forEach(p => p.classList.remove("active"));
      tab.classList.add("active");
      const pane = document.getElementById(tab.dataset.pane);
      if (pane) pane.classList.add("active");
    });
  });
}

// Logs
function addLog(msg, level = "info") {
  const pane = document.getElementById("logs-pane");
  if (!pane) return;
  const time = new Date().toTimeString().slice(0, 8);
  const row = document.createElement("div");
  row.className = `log-line ${level}`;
  row.innerHTML = `<span class="log-time">${time}</span><span class="log-msg">${escHtml(msg)}</span>`;
  pane.appendChild(row);
  pane.scrollTop = pane.scrollHeight;
}

// Terminal
function addTerminalLine(text, type = "output") {
  const pane = document.getElementById("terminal-pane");
  if (!pane) return;
  const line = document.createElement("div");
  line.className = `terminal-line ${type}`;
  line.textContent = text;
  pane.appendChild(line);
  pane.scrollTop = pane.scrollHeight;
}

// Tests
function addTestResult(name, passed) {
  const pane = document.getElementById("tests-pane");
  if (!pane) return;
  const item = document.createElement("div");
  item.className = `test-item ${passed ? "pass" : "fail"}`;
  item.innerHTML = `
    <span class="test-icon">${passed ? "✅" : "❌"}</span>
    <span>${escHtml(name)}</span>`;
  pane.appendChild(item);
  pane.scrollTop = pane.scrollHeight;
  telemetry.tests++;
  updateTelemetryUI();
}

// Git
function addGitCommit(hash, message, author) {
  const pane = document.getElementById("git-pane");
  if (!pane) return;
  const item = document.createElement("div");
  item.className = "git-commit";
  item.innerHTML = `
    <span class="git-hash">${escHtml((hash || "").slice(0, 7))}</span>
    <span class="git-msg">${escHtml(message || "")}</span>
    <span class="git-author">${escHtml(author || "AgentVerse")}</span>`;
  pane.prepend(item);
}

// Chat
function initChat() {
  const input  = document.getElementById("chat-input");
  const submit = document.getElementById("chat-submit");

  const send = () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    submit.disabled = true;
    addChatMessage("user", text);
    // Send both to chat and as task if it starts with "Build" / imperative
    if (/^build|^create|^make|^write|^generate|^implement/i.test(text)) {
      wsSend({ type: "run_task", goal: text });
      setMode("TASK");
      addLog(`Task started: ${text}`, "agent");
      setPipelineStage("planning");
    } else {
      wsSend({ type: "chat", text });
    }
    // Start new assistant message
    state.activeChatMsg = addChatMessage("assistant", "");
    state.chatBuffer = "";
  };

  submit.addEventListener("click", send);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  });
  input.addEventListener("input", () => {
    submit.disabled = !input.value.trim();
  });
  submit.disabled = true;
}

function addChatMessage(role, text) {
  const pane = document.getElementById("chat-messages");
  if (!pane) return null;

  const msg = document.createElement("div");
  msg.className = `chat-msg ${role}`;
  const roleLabel = role === "user" ? "👤 You" : role === "assistant" ? "◈ AgentVerse" : "System";
  msg.innerHTML = `
    <div class="chat-msg-role">${roleLabel}</div>
    <div class="chat-msg-body">${escHtml(text)}</div>`;
  pane.appendChild(msg);
  pane.scrollTop = pane.scrollHeight;
  // Switch to chat pane
  activateBottomPane("chat-pane");
  return msg;
}

function appendChatToken(token) {
  if (!state.activeChatMsg) {
    state.activeChatMsg = addChatMessage("assistant", "");
  }
  state.chatBuffer += token;
  const body = state.activeChatMsg.querySelector(".chat-msg-body");
  if (body) body.textContent = state.chatBuffer;
  const pane = document.getElementById("chat-messages");
  if (pane) pane.scrollTop = pane.scrollHeight;
}

function finalizeChatMessage(text) {
  if (state.activeChatMsg) {
    const body = state.activeChatMsg.querySelector(".chat-msg-body");
    if (body && text) body.textContent = text;
    state.activeChatMsg = null;
    state.chatBuffer = "";
  }
  document.getElementById("chat-submit").disabled = false;
}

function activateBottomPane(paneId) {
  const tab = document.querySelector(`.bottom-tab[data-pane="${paneId}"]`);
  if (tab && !tab.classList.contains("active")) tab.click();
}

// ══════════════════════════════════════════════════════════════
// 10. TOAST
// ══════════════════════════════════════════════════════════════
function showToast(msg, type = "info", duration = 3000) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    toast.style.transition = "all 0.3s";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ══════════════════════════════════════════════════════════════
// 11. EVENT ROUTING
// ══════════════════════════════════════════════════════════════
function routeEvent(msg) {
  const { type, data } = msg;

  switch (type) {
    case "connected": {
      if (data.model)     document.getElementById("header-model").textContent    = data.model;
      if (data.workspace) document.getElementById("header-workspace").textContent = data.workspace;
      if (data.branch)    document.getElementById("header-branch").textContent    = `⎇ ${data.branch}`;
      addLog(`Connected — workspace: ${data.workspace || "devpilot"}, model: ${data.model || "?"}`, "success");
      break;
    }

    case "file_tree":
      renderFileTree(data);
      break;

    case "file_content": {
      const { path, content, language } = data;
      openFileInEditor(path, content, language);
      break;
    }

    case "agent_started":
    case "AgentStarted": {
      const name = data.agent_name || "";
      setAgentStatus(name, "running", "Starting up…");
      addLog(`▶ ${name} agent started`, "agent");
      setPipelineStage(name);
      setMode("TASK");
      document.getElementById("header-active-agent").textContent = name;
      break;
    }

    case "agent_step":
    case "AgentStep": {
      const name = data.agent_name || "";
      const step = data.step || "";
      const id = resolveAgentId(name);
      if (id) {
        const taskEl = document.getElementById(`agt-${id}`);
        if (taskEl) taskEl.textContent = step.slice(0, 50);
      }
      addLog(`  ✓ ${name}: ${step}`, "info");
      break;
    }

    case "agent_progress":
    case "AgentProgress": {
      const name  = data.agent_name || "";
      const pct   = data.progress_pct || 0;
      const token = data.llm_token;
      if (pct) updateAgentProgress(name, pct);
      if (token) appendChatToken(token);
      break;
    }

    case "agent_finished":
    case "AgentFinished": {
      const name = data.agent_name || "";
      setAgentStatus(name, "done");
      completePipelineStage(name);
      addLog(`✓ ${name} agent finished`, "success");
      break;
    }

    case "task_started":
    case "TaskStarted": {
      const goal = data.goal || "";
      addLog(`🚀 Pipeline started: ${goal}`, "agent");
      addTerminalLine(`$ agentverse run "${goal}"`, "cmd");
      setPipelineStage("planning");
      break;
    }

    case "task_complete":
    case "TaskComplete": {
      const success = data.success;
      const files   = data.written_files || [];
      setPipelineStage("done");
      completePipelineStage("done");
      setMode("CHAT");
      telemetry.files += files.length;
      updateTelemetryUI();
      if (success) {
        showToast(`✓ Pipeline complete — ${files.length} files written`, "success", 5000);
        addLog(`Pipeline complete. Files: ${files.length}`, "success");
        addTerminalLine("$ Done!", "output");
      } else {
        showToast("Pipeline finished with errors", "error");
        addLog("Pipeline finished with errors", "error");
      }
      // Reload file tree
      setTimeout(() => wsSend({ type: "get_files" }), 800);
      break;
    }

    case "file_creating": {
      const path    = data.path || data.file_path || "";
      const content = data.content || "";
      const lang    = data.language || detectLang(path);
      addFileToTree(path);
      addFileActivity(path, "creating");
      addLog(`+ Creating ${path}`, "file");
      telemetry.files++;
      if (content) {
        const lines = content.split("\n").length;
        telemetry.loc += lines;
        updateTelemetryUI();
        liveTypeContent(path, content, lang);
      }
      break;
    }

    case "file_editing": {
      const path    = data.path || data.file_path || "";
      const content = data.content || "";
      const lang    = detectLang(path);
      highlightFileInTree(path, "glowing");
      addFileActivity(path, "editing");
      addLog(`✏ Editing ${path}`, "file");
      if (content) liveTypeContent(path, content, lang);
      break;
    }

    case "file_reading": {
      const path = data.path || data.file_path || "";
      addFileActivity(path, "read");
      break;
    }

    case "file_confirmed": {
      const path = data.path || "";
      highlightFileInTree(path, "saved");
      finishFileActivity(path, "creating");
      finishFileActivity(path, "editing");
      addLog(`✓ Saved ${path}`, "success");
      addTerminalLine(`  Wrote ${path}`, "output");
      break;
    }

    case "PipelineStarted": {
      const stages = data.stages || [];
      stages.forEach(s => {
        const el = document.querySelector(`[data-stage-name="${s}"]`);
        if (el) el.classList.add("active");
      });
      break;
    }

    case "PipelineStageChanged": {
      const stage = data.stage || "";
      setPipelineStage(stage);
      addLog(`Pipeline → ${stage}`, "info");
      break;
    }

    case "GitHubConfirmRequest": {
      const ok = confirm(`AgentVerse wants to commit & push:\n\n${JSON.stringify(data, null, 2)}\n\nAllow?`);
      wsSend({ type: "github_confirm", accepted: ok });
      break;
    }

    case "error":
    case "Error": {
      const errMsg = data.message || data.error || "Unknown error";
      addLog(`✗ ${errMsg}`, "error");
      showToast(errMsg, "error");
      const agentName = data.agent_name || "";
      if (agentName) setAgentStatus(agentName, "failed");
      break;
    }

    case "warning":
    case "Warning": {
      addLog(`⚠ ${data.message || ""}`, "warn");
      break;
    }

    case "chat_token":
      appendChatToken(data.token || "");
      break;

    case "chat_done":
      finalizeChatMessage(data.text || "");
      break;

    default:
      break;
  }
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════
function setConnStatus(online) {
  const dot   = document.getElementById("conn-dot");
  const label = document.getElementById("conn-label");
  if (dot)   { dot.className = online ? "online" : "offline"; }
  if (label) { label.textContent = online ? "Connected" : "Connecting…"; }
}

function setMode(mode) {
  const badge = document.getElementById("mode-badge");
  if (!badge) return;
  badge.textContent = mode;
  badge.classList.toggle("task", mode === "TASK");
}

function detectLang(path) {
  const ext = path.split(".").pop().toLowerCase();
  return {
    py: "python", js: "javascript", jsx: "javascript",
    ts: "typescript", tsx: "typescript", html: "html",
    css: "css", json: "json", yaml: "yaml", yml: "yaml",
    md: "markdown", sh: "shell", bash: "shell",
    toml: "toml", rs: "rust", go: "go",
  }[ext] || "plaintext";
}

function escHtml(str) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// ══════════════════════════════════════════════════════════════
// 12. INIT
// ══════════════════════════════════════════════════════════════
function init() {
  buildPipelineBar();
  buildAgentCards();
  initBottomTabs();
  initChat();
  connectWS();
  initMonaco();

  // Header tooltip active
  document.getElementById("mode-badge")?.addEventListener("click", () => {
    activateBottomPane("chat-pane");
    document.getElementById("chat-input")?.focus();
  });

  // Explorer search
  document.getElementById("explorer-search-input")?.addEventListener("input", function () {
    const q = this.value.toLowerCase();
    document.querySelectorAll("#file-tree .tree-item").forEach(item => {
      const name = (item.querySelector(".tree-name")?.textContent || "").toLowerCase();
      item.style.display = !q || name.includes(q) ? "" : "none";
    });
  });

  // Add initial terminal welcome
  addTerminalLine("  ◈  AgentVerse Web IDE — Ready", "cmd");
  addTerminalLine("  Type a task in the Chat tab to start building.", "output");
  addLog("AgentVerse Web IDE initialized", "info");
}

window.addEventListener("DOMContentLoaded", init);
