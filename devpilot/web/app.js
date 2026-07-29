(function(){
  "use strict";

  /* ================= AGENT DEFINITIONS ================= */
  var AGENTS = [
    {id:'planner',   name:'Planner',       icon:'🧠', color:'var(--c-planner)',   idle:'awaiting request'},
    {id:'architect', name:'Architect',     icon:'🏗️', color:'var(--c-architect)', idle:'no structure yet'},
    {id:'coder',     name:'Coder',         icon:'💻', color:'var(--c-coder)',     idle:'no files streamed'},
    {id:'validator', name:'Validator',     icon:'🔍', color:'var(--c-validator)', idle:'nothing to check'},
    {id:'tester',    name:'Tester',        icon:'🧪', color:'var(--c-tester)',    idle:'no suite run'},
    {id:'reviewer',  name:'Reviewer',      icon:'🧐', color:'var(--c-reviewer)',  idle:'no diff reviewed'},
    {id:'docs',      name:'Documentation', icon:'📖', color:'var(--c-docs)',      idle:'README untouched'},
    {id:'github',    name:'GitHub',        icon:'🐙', color:'var(--c-github)',    idle:'no commit staged'}
  ];

  /* ================= PROJECT FALLBACK TEMPLATES ================= */
  function healthTemplate(){
    return {
      id:'health', label:'personal-health-dashboard',
      plan:[
        'Parse request: dashboard for steps, heart rate, sleep, hydration',
        'No backend requested — single-page static build',
        'Target stack: semantic HTML5 + vanilla CSS + vanilla JS'
      ],
      files:[
        {path:'index.html', agent:'coder', lang:'html', content:
`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Health Dashboard</title>
</head>
<body>
  <header class="topbar">
    <h1>Health Dashboard</h1>
    <span id="clock" class="clock"></span>
  </header>

  <main class="grid">
    <section class="card">
      <span class="label">Steps</span>
      <span class="value" id="steps">0</span>
      <div class="bar"><div class="bar-fill" id="stepsBar"></div></div>
    </section>

    <section class="card">
      <span class="label">Heart Rate</span>
      <span class="value" id="hr">0<small> bpm</small></span>
      <div class="bar"><div class="bar-fill" id="hrBar"></div></div>
    </section>

    <section class="card">
      <span class="label">Sleep</span>
      <span class="value" id="sleep">0<small> hrs</small></span>
      <div class="bar"><div class="bar-fill" id="sleepBar"></div></div>
    </section>

    <section class="card">
      <span class="label">Hydration</span>
      <span class="value" id="water">0<small> / 8 cups</small></span>
      <div class="bar"><div class="bar-fill" id="waterBar"></div></div>
    </section>
  </main>

  <footer>Synced <span id="synced">just now</span></footer>
</body>
</html>
`},
        {path:'style.css', agent:'coder', lang:'css', content:
`* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, Segoe UI, Roboto, sans-serif;
  background: #f4f6f8;
  color: #1c2230;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  background: #12151d;
  color: #eef1f5;
}
.topbar h1 { font-size: 18px; margin: 0; }
.clock { font-size: 12px; color: #6ee7c8; font-family: monospace; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  padding: 24px;
}
.card {
  background: #fff;
  border-radius: 12px;
  padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.card .label { font-size: 12px; color: #6b7385; letter-spacing: .4px; text-transform: uppercase; }
.card .value { font-size: 28px; font-weight: 700; }
.card .value small { font-size: 13px; font-weight: 500; color: #6b7385; }
.bar { height: 6px; border-radius: 4px; background: #e7ebef; overflow: hidden; }
.bar-fill { height: 100%; width: 0%; background: #2fbf9a; transition: width 1.1s ease; }

footer { text-align: center; padding: 14px; font-size: 11px; color: #99a1ad; }
`},
        {path:'script.js', agent:'coder', lang:'js', content:
`function animateValue(el, target, suffix) {
  let cur = 0;
  const step = Math.max(1, Math.round(target / 40));
  const t = setInterval(() => {
    cur += step;
    if (cur >= target) { cur = target; clearInterval(t); }
    el.textContent = cur + (suffix || '');
  }, 20);
}

const data = { steps: 8420, stepsGoal: 10000, hr: 72, sleep: 7.2, water: 5 };

animateValue(document.getElementById('steps'), data.steps);
document.getElementById('stepsBar').style.width = (data.steps / data.stepsGoal * 100) + '%';

document.getElementById('hr').innerHTML = data.hr + '<small> bpm</small>';
document.getElementById('hrBar').style.width = '64%';

document.getElementById('sleep').innerHTML = data.sleep + '<small> hrs</small>';
document.getElementById('sleepBar').style.width = (data.sleep / 9 * 100) + '%';

document.getElementById('water').innerHTML = data.water + '<small> / 8 cups</small>';
document.getElementById('waterBar').style.width = (data.water / 8 * 100) + '%';

function tickClock() {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();
}
tickClock();
setInterval(tickClock, 1000);
`},
        {path:'README.md', agent:'docs', lang:'md', content:
`# Personal Health Dashboard

A single-page dashboard that surfaces steps, heart rate, sleep and hydration
at a glance. Generated by the DevPilot Coder agent, static HTML/CSS/JS,
no build step required — open `+'`index.html`'+` directly.
`}
      ]
    };
  }

  function iotTemplate(){
    return {
      id:'iot', label:'iot-sensor-monitor',
      plan:[
        'Parse request: live monitor for temperature, humidity, signal',
        'No hardware bridge available — simulate live values client-side',
        'Target stack: vanilla HTML/CSS/JS, dark operator console styling'
      ],
      files:[
        {path:'index.html', agent:'coder', lang:'html', content:
`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Sensor Monitor</title>
</head>
<body>
  <header>
    <h1>IoT Sensor Monitor</h1>
    <span class="badge" id="connBadge">● connected</span>
  </header>

  <main class="grid">
    <div class="metric">
      <span class="label">Temperature</span>
      <span class="value"><span id="temp">--</span>°C</span>
      <div class="track"><div class="fill" id="tempFill"></div></div>
    </div>
    <div class="metric">
      <span class="label">Humidity</span>
      <span class="value"><span id="hum">--</span>%</span>
      <div class="track"><div class="fill" id="humFill"></div></div>
    </div>
    <div class="metric">
      <span class="label">Motion</span>
      <span class="value" id="motion">idle</span>
      <div class="track"><div class="fill" id="motionFill"></div></div>
    </div>
    <div class="metric">
      <span class="label">Signal (RSSI)</span>
      <span class="value"><span id="rssi">--</span> dBm</span>
      <div class="track"><div class="fill" id="rssiFill"></div></div>
    </div>
  </main>

  <section class="log">
    <div class="log-head">device log</div>
    <div id="logBody"></div>
  </section>
</body>
</html>
`},
        {path:'style.css', agent:'coder', lang:'css', content:
`* { box-sizing: border-box; }
body {
  margin: 0;
  background: #0b0e14;
  color: #d7dce5;
  font-family: 'JetBrains Mono', monospace;
}
header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 24px; border-bottom: 1px solid #232a38;
}
header h1 { font-size: 15px; margin: 0; letter-spacing: .4px; }
.badge { font-size: 11px; color: #6ee7c8; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px; padding: 20px 24px;
}
.metric {
  background: #11151d; border: 1px solid #232a38; border-radius: 8px;
  padding: 14px 16px; display: flex; flex-direction: column; gap: 8px;
}
.metric .label { font-size: 10.5px; color: #6b7385; text-transform: uppercase; letter-spacing: 1px; }
.metric .value { font-size: 22px; font-weight: 700; color: #f2b866; }
.track { height: 5px; background: #1c2230; border-radius: 3px; overflow: hidden; }
.fill { height: 100%; width: 30%; background: #67d0f2; transition: width .6s ease; }

.log { margin: 0 24px 24px; border: 1px solid #232a38; border-radius: 8px; background: #11151d; }
.log-head { padding: 8px 14px; font-size: 10.5px; color: #6b7385; border-bottom: 1px solid #232a38; letter-spacing: 1px;}
#logBody { max-height: 140px; overflow-y: auto; padding: 8px 14px; font-size: 11px; color: #8b93a3; line-height: 1.8; }
`},
        {path:'script.js', agent:'coder', lang:'js', content:
`function rand(min, max) { return Math.random() * (max - min) + min; }

const state = { temp: 22.4, hum: 46, rssi: -58 };

function log(msg) {
  const el = document.getElementById('logBody');
  const line = document.createElement('div');
  const t = new Date().toLocaleTimeString();
  line.textContent = '[' + t + ']  ' + msg;
  el.prepend(line);
  while (el.childNodes.length > 30) el.removeChild(el.lastChild);
}

function tick() {
  state.temp += rand(-0.3, 0.3);
  state.hum += rand(-1, 1);
  state.rssi += rand(-2, 2);

  document.getElementById('temp').textContent = state.temp.toFixed(1);
  document.getElementById('tempFill').style.width = Math.min(100, state.temp * 2) + '%';

  document.getElementById('hum').textContent = Math.round(state.hum);
  document.getElementById('humFill').style.width = state.hum + '%';

  document.getElementById('rssi').textContent = Math.round(state.rssi);
  document.getElementById('rssiFill').style.width = (100 + state.rssi) + '%';

  const moving = Math.random() > 0.7;
  document.getElementById('motion').textContent = moving ? 'motion' : 'idle';
  document.getElementById('motionFill').style.width = moving ? '90%' : '10%';
  if (moving) log('PIR sensor triggered');
}

log('device online, streaming telemetry');
tick();
setInterval(tick, 1600);
`},
        {path:'README.md', agent:'docs', lang:'md', content:
`# IoT Sensor Monitor

Live operator console for temperature, humidity, motion and signal
strength. Values are simulated client-side for this demo build —
swap `+'`script.js`'+` for a WebSocket/MQTT bridge to attach real hardware.
`}
      ]
    };
  }

  function portfolioTemplate(){
    return {
      id:'portfolio', label:'portfolio-site',
      plan:[
        'Parse request: single-page personal portfolio',
        'Sections: hero, projects, contact',
        'Target stack: vanilla HTML/CSS/JS'
      ],
      files:[
        {path:'index.html', agent:'coder', lang:'html', content:
`<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Portfolio</title></head>
<body>
  <header class="hero">
    <h1>Your Name</h1>
    <p>Building things at the edge of code and curiosity.</p>
  </header>
  <main class="projects" id="projects"></main>
  <footer>
    <a href="#">GitHub</a> · <a href="#">Email</a>
  </footer>
</body>
</html>
`},
        {path:'style.css', agent:'coder', lang:'css', content:
`* { box-sizing: border-box; }
body { margin:0; font-family: -apple-system, Segoe UI, sans-serif; background:#0b0e14; color:#d7dce5; }
.hero { text-align:center; padding:70px 20px 40px; }
.hero h1 { font-size:32px; margin:0 0 8px; }
.hero p { color:#6b7385; }
.projects { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; padding:20px 32px; }
.project-card { background:#11151d; border:1px solid #232a38; border-radius:10px; padding:18px; }
.project-card h3 { margin:0 0 6px; font-size:14px; }
.project-card p { margin:0; font-size:12px; color:#6b7385; }
footer { text-align:center; padding:30px; font-size:12px; color:#6b7385; }
footer a { color:#6ee7c8; text-decoration:none; }
`},
        {path:'script.js', agent:'coder', lang:'js', content:
`const projects = [
  { name: 'Project One', desc: 'A short description of what this project does.' },
  { name: 'Project Two', desc: 'A short description of what this project does.' },
  { name: 'Project Three', desc: 'A short description of what this project does.' }
];

const el = document.getElementById('projects');
projects.forEach(p => {
  const card = document.createElement('div');
  card.className = 'project-card';
  card.innerHTML = '<h3>' + p.name + '</h3><p>' + p.desc + '</p>';
  el.appendChild(card);
});
`},
        {path:'README.md', agent:'docs', lang:'md', content:
`# Portfolio Site

One-page portfolio scaffold — swap in real project data and links.
`}
      ]
    };
  }

  function genericTemplate(promptText){
    var title = (promptText || 'New Project').trim();
    title = title.length > 46 ? title.slice(0,46) + '…' : title;
    var titleCase = title.charAt(0).toUpperCase() + title.slice(1);
    return {
      id:'generic', label:'generated-app',
      plan:[
        'Parse request: "' + titleCase + '"',
        'No specialised template matched — scaffolding a general landing page',
        'Target stack: vanilla HTML/CSS/JS'
      ],
      files:[
        {path:'index.html', agent:'coder', lang:'html', content:
`<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>`+titleCase+`</title></head>
<body>
  <header class="hero">
    <h1>`+titleCase+`</h1>
    <p>Scaffolded by DevPilot from your prompt.</p>
    <button id="cta">Get started</button>
  </header>
  <main class="features">
    <div class="feature"><h3>Fast</h3><p>Lightweight, dependency-free build.</p></div>
    <div class="feature"><h3>Simple</h3><p>Readable HTML, CSS and JS you can extend.</p></div>
    <div class="feature"><h3>Yours</h3><p>Every file is editable in the panel on the left.</p></div>
  </main>
</body>
</html>
`},
        {path:'style.css', agent:'coder', lang:'css', content:
`* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system, Segoe UI, sans-serif; background:#0b0e14; color:#d7dce5; }
.hero { text-align:center; padding:80px 24px 50px; }
.hero h1 { font-size:30px; margin:0 0 10px; }
.hero p { color:#6b7385; margin:0 0 20px; }
#cta { background:#6ee7c8; color:#08110d; border:0; padding:11px 22px; border-radius:6px; font-weight:700; cursor:pointer; }
.features { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; padding:0 32px 50px; }
.feature { background:#11151d; border:1px solid #232a38; border-radius:10px; padding:18px; }
.feature h3 { margin:0 0 6px; font-size:14px; color:#6ee7c8; }
.feature p { margin:0; font-size:12px; color:#6b7385; }
`},
        {path:'script.js', agent:'coder', lang:'js', content:
`document.getElementById('cta').addEventListener('click', function () {
  this.textContent = 'Nice — you clicked it';
  this.disabled = true;
});
`},
        {path:'README.md', agent:'docs', lang:'md', content:
`# `+titleCase+`

Generated by the DevPilot Coder agent from a free-text prompt.
`}
      ]
    };
  }

  function pickTemplate(text){
    var t = (text || '').toLowerCase();
    if (/health|dashboard|fitness|workout/.test(t)) return healthTemplate();
    if (/iot|sensor|device|arduino|esp32|mqtt/.test(t)) return iotTemplate();
    if (/portfolio|resume|cv/.test(t)) return portfolioTemplate();
    return genericTemplate(text);
  }

  /* ================= DOM REFS ================= */
  var el = {
    tree: document.getElementById('tree'),
    projLabel: document.getElementById('projLabel'),
    editorTabs: document.getElementById('editorTabs'),
    editorScroll: document.getElementById('editorScroll'),
    editorEmpty: document.getElementById('editorEmpty'),
    agentList: document.getElementById('agentList'),
    telemetry: document.getElementById('telemetry'),
    progressStrip: document.getElementById('progressStrip'),
    previewFrame: document.getElementById('previewFrame'),
    previewEmpty: document.getElementById('previewEmpty'),
    previewWrap: document.getElementById('previewWrap'),
    urlText: document.getElementById('urlText'),
    promptInput: document.getElementById('promptInput'),
    sendBtn: document.getElementById('sendBtn'),
    statusLeft: document.getElementById('statusLeft'),
    busState: document.getElementById('busState'),
    modelLed: document.getElementById('modelLed'),
    modelProvider: document.getElementById('modelProvider'),
    modelName: document.getElementById('modelName'),
    btnDesktop: document.getElementById('btnDesktop'),
    btnMobile: document.getElementById('btnMobile'),
    btnRefresh: document.getElementById('btnRefresh'),
    btnPopout: document.getElementById('btnPopout')
  };

  var filesState = {};      // path -> content (final)
  var fileOrder = [];       // explorer order
  var activePath = null;
  var running = false;
  var socket = null;

  /* ================= BUILD STATIC PANELS ================= */
  AGENTS.forEach(function(a){
    var card = document.createElement('div');
    card.className = 'agent-card';
    card.id = 'agent-' + a.id;
    card.innerHTML =
      '<span class="a-dot" style="background:' + a.color + '"></span>' +
      '<div class="a-main"><div class="a-name">' + a.icon + ' ' + a.name + '</div>' +
      '<div class="a-sub" id="agent-sub-' + a.id + '">' + a.idle + '</div></div>' +
      '<div class="a-state" id="agent-state-' + a.id + '">IDLE</div>';
    el.agentList.appendChild(card);
  });

  for (var i=0;i<8;i++){
    var seg = document.createElement('div');
    seg.className = 'seg';
    seg.id = 'seg-' + i;
    el.progressStrip.appendChild(seg);
  }

  /* ================= AGENT ID MAPPER ================= */
  function mapAgentId(name){
    var n = String(name || '').toLowerCase().trim();
    if (n === 'planner') return 'planner';
    if (n === 'architect') return 'architect';
    if (n === 'coder') return 'coder';
    if (n === 'validator') return 'validator';
    if (n === 'tester') return 'tester';
    if (n === 'reviewer') return 'reviewer';
    if (n === 'docs' || n === 'documentation') return 'docs';
    if (n === 'github') return 'github';
    return 'coder';
  }

  function getSegmentIndex(agentId){
    var order = ['planner','architect','coder','validator','tester','reviewer','docs','github'];
    var idx = order.indexOf(agentId);
    return idx > -1 ? idx + 1 : 1;
  }

  /* ================= HELPERS ================= */
  function escapeHtml(s){
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function lightHighlight(escaped){
    return escaped
      .replace(/(&quot;|"|')([^\n]*?)\1/g, function(m){ return '<span class="tok-str">'+m+'</span>'; })
      .replace(/(\/\/[^\n]*)/g, '<span class="tok-com">$1</span>')
      .replace(/(&lt;!--[\s\S]*?--&gt;)/g, '<span class="tok-com">$1</span>');
  }

  function setAgentStatus(id, status, subtext){
    var card = document.getElementById('agent-' + id);
    var stateEl = document.getElementById('agent-state-' + id);
    var subEl = document.getElementById('agent-sub-' + id);
    if (!card) return;
    card.classList.remove('active','done');
    if (status === 'active'){ card.classList.add('active'); stateEl.textContent = 'WORKING'; }
    else if (status === 'done'){ card.classList.add('done'); stateEl.textContent = 'DONE'; }
    else { stateEl.textContent = 'IDLE'; }
    if (subtext) subEl.textContent = subtext;
  }

  function lightSegments(count){
    for (var i=0;i<8;i++){
      var seg = document.getElementById('seg-'+i);
      if (seg) seg.classList.toggle('on', i < count);
    }
  }

  function log(agentId, html, isUser){
    var meta = AGENTS.filter(function(a){return a.id===agentId;})[0];
    var line = document.createElement('div');
    line.className = 'tlog' + (isUser ? ' user' : '');
    var ts = new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
    var tag = isUser ? 'you' : (meta ? meta.name : agentId);
    line.style.borderLeftColor = isUser ? 'var(--mint)' : (meta ? meta.color : 'var(--line)');
    line.innerHTML = '<span class="ts">' + ts + '</span><b>' + tag + '</b> — ' + html;
    el.telemetry.appendChild(line);
    el.telemetry.scrollTop = el.telemetry.scrollHeight;
  }

  function sleep(ms){ return new Promise(function(res){ setTimeout(res, ms); }); }

  /* ================= EXPLORER ================= */
  function resetExplorer(projectLabel){
    el.tree.innerHTML = '';
    el.projLabel.textContent = projectLabel;
    fileOrder = [];
  }

  function addExplorerEntry(path){
    if (!path || fileOrder.indexOf(path) > -1) return;
    fileOrder.push(path);
    var li = document.createElement('li');
    li.className = 'tree-item';
    li.id = 'tree-' + cssSafe(path);
    li.innerHTML = '<span class="branch">├─</span><span class="fname">' + path + '</span><span class="status-dot pending" id="dot-' + cssSafe(path) + '"></span>';
    li.addEventListener('click', function(){
      openTab(path);
    });
    el.tree.appendChild(li);
  }

  function renderTreeFromNode(node){
    if (!node) return;
    if (node.type === 'file' && node.name) {
      var p = node.path || node.name;
      // strip leading ./ if present
      p = p.replace(/^\.\//, '');
      addExplorerEntry(p);
      setFileDotStatus(p, 'done');
    } else if (node.type === 'dir' && node.children) {
      node.children.forEach(renderTreeFromNode);
    }
  }

  function cssSafe(path){ return String(path || '').replace(/[^a-zA-Z0-9]/g,'_'); }

  function setFileDotStatus(path, status){
    var dot = document.getElementById('dot-' + cssSafe(path));
    if (dot) dot.className = 'status-dot ' + status;
  }

  function setTreeActive(path){
    var items = el.tree.querySelectorAll('.tree-item');
    items.forEach(function(it){ it.classList.remove('active'); });
    var cur = document.getElementById('tree-' + cssSafe(path));
    if (cur) cur.classList.add('active');
  }

  /* ================= EDITOR ================= */
  function ensureTab(path){
    if (document.getElementById('tab-' + cssSafe(path))) return;
    var tab = document.createElement('div');
    tab.className = 'editor-tab';
    tab.id = 'tab-' + cssSafe(path);
    tab.innerHTML = '<span class="tab-led" style="background:var(--c-coder)"></span>' + path;
    tab.addEventListener('click', function(){ openTab(path); });
    el.editorTabs.appendChild(tab);
  }

  function openTab(path){
    activePath = path;
    el.editorEmpty.style.display = 'none';
    ensureTab(path);
    var tabs = el.editorTabs.querySelectorAll('.editor-tab');
    tabs.forEach(function(t){ t.classList.remove('active'); });
    var t = document.getElementById('tab-' + cssSafe(path));
    if (t) t.classList.add('active');
    setTreeActive(path);

    if (filesState[path] !== undefined) {
      renderEditorContent(filesState[path], true);
      updatePreview();
    } else {
      // Fetch file content from backend REST API
      fetch('/api/file?path=' + encodeURIComponent(path))
        .then(function(res){ return res.json(); })
        .then(function(data){
          if (data && data.content !== undefined) {
            filesState[path] = data.content;
            if (activePath === path) renderEditorContent(data.content, true);
            updatePreview();
          }
        }).catch(function(){});
    }
  }

  function renderEditorContent(text, finalPass){
    el.editorScroll.innerHTML = '';
    var gutter = document.createElement('div');
    gutter.className = 'gutter';
    var lines = (text || '').split('\n');
    gutter.innerHTML = lines.map(function(_,i){ return '<div>'+(i+1)+'</div>'; }).join('');
    var code = document.createElement('pre');
    code.className = 'editor-code';
    var escaped = escapeHtml(text);
    code.innerHTML = finalPass ? lightHighlight(escaped) : escaped;
    if (!finalPass) {
      var cur = document.createElement('span');
      cur.className = 'cursor-blink';
      cur.textContent = '\u00A0';
      code.appendChild(cur);
    }
    el.editorScroll.appendChild(gutter);
    el.editorScroll.appendChild(code);
    el.editorScroll.scrollTop = el.editorScroll.scrollHeight;
  }

  function typewrite(path, fullText){
    return new Promise(function(resolve){
      ensureTab(path);
      openTab(path);
      var i = 0;
      var chunk = Math.max(2, Math.round(fullText.length / 140));
      var timer = setInterval(function(){
        i += chunk;
        var partial = fullText.slice(0, i);
        filesState[path] = partial;
        if (activePath === path) renderEditorContent(partial, false);
        if (i >= fullText.length){
          clearInterval(timer);
          filesState[path] = fullText;
          if (activePath === path) renderEditorContent(fullText, true);
          resolve();
        }
      }, 12);
    });
  }

  /* ================= PREVIEW ENGINE ================= */
  function buildPreviewDoc(){
    var html = filesState['index.html'];
    if (!html) {
      // Find any html file in filesState
      var htmlKeys = Object.keys(filesState).filter(function(k){ return k.endsWith('.html'); });
      if (htmlKeys.length > 0) html = filesState[htmlKeys[0]];
    }
    if (!html) return null;

    var css = filesState['style.css'] || '';
    var js = filesState['script.js'] || '';
    var doc = html;

    if (css && doc.indexOf(css) === -1) {
      doc = doc.indexOf('</head>') > -1 ? doc.replace('</head>', '<style>'+css+'</style></head>') : doc + '<style>'+css+'</style>';
    }
    if (js && doc.indexOf(js) === -1) {
      doc = doc.indexOf('</body>') > -1 ? doc.replace('</body>', '<script>'+js+'<\/script></body>') : doc + '<script>'+js+'<\/script>';
    }
    return doc;
  }

  function updatePreview(){
    var doc = buildPreviewDoc();
    if (!doc) {
      // Try loading index.html from server REST API if not yet in filesState
      fetch('/api/file?path=index.html')
        .then(function(res){ return res.json(); })
        .then(function(data){
          if (data && data.content) {
            filesState['index.html'] = data.content;
            renderPreviewDoc(buildPreviewDoc());
          }
        }).catch(function(){});
      return;
    }
    renderPreviewDoc(doc);
  }

  function renderPreviewDoc(doc){
    if (!doc) return;
    el.previewEmpty.style.display = 'none';
    el.previewFrame.style.display = 'block';
    el.previewFrame.srcdoc = doc;
    el.urlText.innerHTML = '<span class="live-tag">●&nbsp;live</span>localhost:5500/index.html';
  }

  el.btnRefresh.addEventListener('click', function(){
    updatePreview();
  });
  el.btnPopout.addEventListener('click', function(){
    var doc = buildPreviewDoc();
    if (!doc) return;
    var blob = new Blob([doc], {type:'text/html'});
    window.open(URL.createObjectURL(blob), '_blank');
  });
  el.btnMobile.addEventListener('click', function(){
    el.previewWrap.classList.add('mobile');
    el.btnMobile.classList.add('on'); el.btnDesktop.classList.remove('on');
  });
  el.btnDesktop.addEventListener('click', function(){
    el.previewWrap.classList.remove('mobile');
    el.btnDesktop.classList.add('on'); el.btnMobile.classList.remove('on');
  });
  el.btnDesktop.classList.add('on');

  /* ================= INITIAL WORKSPACE SYNC ================= */
  function syncWorkspaceFiles(){
    fetch('/api/files')
      .then(function(res){ return res.json(); })
      .then(function(treeData){
        if (treeData) {
          if (treeData.name && el.projLabel) el.projLabel.textContent = treeData.name;
          if (treeData.children) {
            treeData.children.forEach(renderTreeFromNode);
          }
        }
      }).catch(function(){});

    // Auto load key preview files
    ['index.html', 'style.css', 'script.js', 'README.md'].forEach(function(p){
      fetch('/api/file?path=' + p)
        .then(function(res){ return res.json(); })
        .then(function(data){
          if (data && data.content) {
            filesState[p] = data.content;
            addExplorerEntry(p);
            setFileDotStatus(p, 'done');
            if (!activePath && p === 'index.html') openTab('index.html');
            updatePreview();
          }
        }).catch(function(){});
    });
  }

  /* ================= FALLBACK SIMULATION PIPELINE ================= */
  async function runFallbackPipeline(promptText){
    if (running) return;
    running = true;
    el.sendBtn.disabled = true;
    el.busState.textContent = 'streaming';

    var tpl = pickTemplate(promptText);

    filesState = {};
    activePath = null;
    resetExplorer(tpl.label);
    el.editorTabs.innerHTML = '';
    el.editorScroll.innerHTML = '';
    el.editorEmpty.style.display = 'flex';
    el.previewFrame.style.display = 'none';
    el.previewFrame.srcdoc = '';
    el.previewEmpty.style.display = 'flex';
    el.previewEmpty.textContent = 'Waiting for index.html…';
    el.urlText.textContent = 'localhost:5500 — build in progress…';
    el.telemetry.innerHTML = '';
    AGENTS.forEach(function(a){ setAgentStatus(a.id,'idle',a.idle); });
    lightSegments(0);

    log('planner', escapeHtml(promptText), true);

    // 1. PLANNER
    setAgentStatus('planner','active','analysing request…');
    el.statusLeft.textContent = 'Planner working · 0 / 8 agents complete';
    await sleep(500);
    for (var p=0;p<tpl.plan.length;p++){
      log('planner', tpl.plan[p]);
      await sleep(260);
    }
    setAgentStatus('planner','done','master plan drafted');
    lightSegments(1);

    // 2. ARCHITECT
    setAgentStatus('architect','active','choosing file structure…');
    el.statusLeft.textContent = 'Architect working · 1 / 8 agents complete';
    await sleep(450);
    tpl.files.forEach(function(f){ addExplorerEntry(f.path); });
    log('architect', 'scaffolding ' + tpl.files.length + ' files: ' + tpl.files.map(function(f){return f.path;}).join(', '));
    await sleep(350);
    setAgentStatus('architect','done', tpl.files.length + ' files planned');
    lightSegments(2);

    // 3. CODER
    setAgentStatus('coder','active','writing files…');
    el.statusLeft.textContent = 'Coder working · 2 / 8 agents complete';
    for (var i=0;i<tpl.files.length;i++){
      var f = tpl.files[i];
      if (f.agent !== 'coder') continue;
      setFileDotStatus(f.path,'active');
      log('coder', 'FilesystemSkill → writing <b>' + f.path + '</b>');
      await typewrite(f.path, f.content);
      setFileDotStatus(f.path,'done');
      log('coder', f.path + ' written (' + f.content.length + ' bytes)');
      if (f.path === 'index.html' || f.path === 'style.css' || f.path === 'script.js') updatePreview();
      await sleep(150);
    }
    setAgentStatus('coder','done', tpl.files.filter(function(f){return f.agent==='coder';}).length + ' files streamed');
    lightSegments(3);

    // 4. VALIDATOR
    setAgentStatus('validator','active','scanning output…');
    el.statusLeft.textContent = 'Validator working · 3 / 8 agents complete';
    await sleep(500);
    log('validator', 'no duplicate paths found');
    await sleep(280);
    log('validator', 'no syntax errors detected');
    setAgentStatus('validator','done','all checks passed');
    lightSegments(4);

    // 5. TESTER
    setAgentStatus('tester','active','running suite…');
    el.statusLeft.textContent = 'Tester working · 4 / 8 agents complete';
    await sleep(500);
    log('tester', 'no test runner configured for static build — smoke-loading index.html');
    await sleep(320);
    log('tester', 'DOM mounts cleanly, 0 console errors');
    setAgentStatus('tester','done','smoke test passed');
    lightSegments(5);

    // 6. REVIEWER
    setAgentStatus('reviewer','active','static analysis…');
    el.statusLeft.textContent = 'Reviewer working · 5 / 8 agents complete';
    await sleep(480);
    log('reviewer', 'no inline secrets or unsafe eval() usage found');
    await sleep(260);
    log('reviewer', 'minor: consider extracting repeated card markup into a helper');
    setAgentStatus('reviewer','done','1 suggestion, 0 blockers');
    lightSegments(6);

    // 7. DOCS
    setAgentStatus('docs','active','writing README…');
    el.statusLeft.textContent = 'Documentation working · 6 / 8 agents complete';
    var readme = tpl.files.filter(function(f){return f.agent==='docs';})[0];
    if (readme){
      addExplorerEntry(readme.path);
      setFileDotStatus(readme.path,'active');
      await typewrite(readme.path, readme.content);
      setFileDotStatus(readme.path,'done');
    }
    log('docs', 'README.md authored');
    setAgentStatus('docs','done','README.md up to date');
    lightSegments(7);

    // 8. GITHUB
    setAgentStatus('github','active','preparing commit…');
    el.statusLeft.textContent = 'GitHub working · 7 / 8 agents complete';
    await sleep(500);
    log('github', 'diff staged: <b>' + tpl.files.length + ' files changed</b>');
    await sleep(260);
    log('github', 'suggested commit message — "feat: scaffold ' + tpl.label + '"');
    setAgentStatus('github','done','ready to commit (approval required)');
    lightSegments(8);

    el.busState.textContent = 'idle';
    el.statusLeft.textContent = 'Build complete · 8 / 8 agents finished';
    running = false;
    el.sendBtn.disabled = false;
  }

  /* ================= WEBSOCKET BACKEND INTEGRATION ================= */
  function connectBackend(){
    try {
      var wsUrl = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws';
      socket = new WebSocket(wsUrl);

      socket.onopen = function(){
        el.busState.textContent = 'connected';
        if (el.modelLed) el.modelLed.classList.remove('offline');
        syncWorkspaceFiles();
      };

      socket.onmessage = function(evt){
        try {
          var msg = JSON.parse(evt.data);
          var type = msg.type;
          var data = msg.data || {};

          if (type === 'connected') {
            if (data.model && el.modelName) el.modelName.textContent = data.model;
            if (data.workspace && el.projLabel) el.projLabel.textContent = data.workspace;
          }
          else if (type === 'file_tree') {
            if (data.name && el.projLabel) el.projLabel.textContent = data.name;
            if (data.children) data.children.forEach(renderTreeFromNode);
            updatePreview();
          }
          else if (type === 'TaskStarted') {
            running = true;
            el.sendBtn.disabled = true;
            el.busState.textContent = 'streaming';
            el.statusLeft.textContent = 'Pipeline starting…';
            log('planner', escapeHtml(data.goal || 'New task started'), true);
            AGENTS.forEach(function(a){ setAgentStatus(a.id, 'idle', a.idle); });
            lightSegments(0);
          }
          else if (type === 'AgentStarted') {
            var agentId = mapAgentId(data.agent_name || data.agent);
            setAgentStatus(agentId, 'active', 'working…');
            lightSegments(getSegmentIndex(agentId));
            el.statusLeft.textContent = (data.agent_name || agentId) + ' working…';
          }
          else if (type === 'AgentStep') {
            var agentId = mapAgentId(data.agent_name || data.agent);
            log(agentId, escapeHtml(data.step || 'Processing…'));
          }
          else if (type === 'AgentProgress') {
            var agentId = mapAgentId(data.agent_name || data.agent);
            if (data.current_milestone) setAgentStatus(agentId, 'active', data.current_milestone);
            if (data.current_file) {
              var p = data.current_file;
              addExplorerEntry(p);
              if (data.llm_token) {
                filesState[p] = (filesState[p] || '') + data.llm_token;
                if (activePath === p) renderEditorContent(filesState[p], false);
                if (p === 'index.html' || p.endsWith('.html')) updatePreview();
              }
            }
          }
          else if (type === 'FileCreating') {
            var p = data.path || data.file_path;
            if (p) {
              addExplorerEntry(p);
              setFileDotStatus(p, 'active');
              log('coder', 'Creating <b>' + escapeHtml(p) + '</b>');
            }
          }
          else if (type === 'FileEditing' || type === 'FileConfirmed') {
            var p = data.path || data.file_path;
            if (p) {
              addExplorerEntry(p);
              setFileDotStatus(p, 'done');
              if (data.content) {
                filesState[p] = data.content;
                openTab(p);
                updatePreview();
              }
            }
          }
          else if (type === 'AgentFinished') {
            var agentId = mapAgentId(data.agent_name || data.agent);
            setAgentStatus(agentId, 'done', 'completed');
          }
          else if (type === 'TaskComplete') {
            running = false;
            el.sendBtn.disabled = false;
            el.busState.textContent = 'idle';
            el.statusLeft.textContent = 'Build complete · 8 / 8 agents finished';
            AGENTS.forEach(function(a){ setAgentStatus(a.id, 'done', 'completed'); });
            lightSegments(8);
            log('github', 'Task complete — <b>' + (data.written_files ? data.written_files.length : 0) + ' files written</b>');
            syncWorkspaceFiles();
            updatePreview();
          }
          else if (type === 'file_content') {
            var p = data.path;
            if (p && data.content !== undefined) {
              filesState[p] = data.content;
              if (activePath === p) renderEditorContent(data.content, true);
              updatePreview();
            }
          }
        } catch(e){}
      };

      socket.onclose = function(){
        el.busState.textContent = 'idle';
        setTimeout(connectBackend, 4000);
      };

      socket.onerror = function(){
        el.busState.textContent = 'idle';
      };
    } catch(e){}
  }

  /* ================= INPUT WIRING ================= */
  function submitPrompt(){
    var v = el.promptInput.value.trim();
    if (!v || running) return;

    if (socket && socket.readyState === WebSocket.OPEN) {
      // Send task directly to Python backend Orchestrator over WebSocket
      socket.send(JSON.stringify({ type: 'run_task', goal: v }));
      running = true;
      el.sendBtn.disabled = true;
      el.busState.textContent = 'streaming';
      el.statusLeft.textContent = 'Pipeline starting…';
      log('planner', escapeHtml(v), true);
    } else {
      // Offline fallback pipeline simulation
      runFallbackPipeline(v);
    }
    el.promptInput.value = '';
  }

  el.sendBtn.addEventListener('click', submitPrompt);
  el.promptInput.addEventListener('keydown', function(e){
    if (e.key === 'Enter') submitPrompt();
  });
  document.querySelectorAll('.chip').forEach(function(chip){
    chip.addEventListener('click', function(){
      if (running) return;
      el.promptInput.value = chip.getAttribute('data-p');
      submitPrompt();
    });
  });

  // Attempt backend connection & initial workspace sync
  connectBackend();
  syncWorkspaceFiles();

})();
