---
marp: true
theme: uncover
paginate: true
size: 16:9
backgroundColor: "#050814"
color: "#ffffff"
style: |
  :root {
    --cyan: #00D4FF;
    --mint: #06D6A0;
    --gold: #FFCC00;
    --crimson: #E63946;
    --muted: rgba(255,255,255,0.6);
    --dim: rgba(255,255,255,0.35);
    --panel: #111B2E;
    --border: #1E3A5F;
  }
  section {
    font-family: "Inter", system-ui, sans-serif;
    text-align: left;
    padding: 64px;
    background: radial-gradient(ellipse at 20% 20%, #0A1533 0%, #050814 85%);
  }
  section.lead {
    background: radial-gradient(ellipse at 50% 50%, #0A1533 0%, #050814 75%);
  }
  section.cover { text-align: center; justify-content: center; }
  h1 { font-size: 64px; font-weight: 800; letter-spacing: -1px; color: #fff; margin: 0; }
  h2 { font-size: 40px; font-weight: 700; color: var(--cyan); margin: 0 0 24px 0; }
  h3 { font-size: 24px; color: var(--mint); font-weight: 600; margin: 0 0 16px 0; }
  .eyebrow { font-family: "JetBrains Mono", monospace; font-size: 14px; letter-spacing: 3px; color: var(--cyan); text-transform: uppercase; }
  .muted { color: var(--muted); }
  .gold { color: var(--gold); }
  .crimson { color: var(--crimson); }
  .mint { color: var(--mint); }
  .cyan { color: var(--cyan); }
  .stat { font-size: 120px; font-weight: 800; color: var(--crimson); letter-spacing: -2px; line-height: 1; }
  .big { font-size: 64px; font-weight: 800; color: var(--gold); line-height: 1; }
  code { background: #111B2E; padding: 2px 8px; border-radius: 4px; color: var(--cyan); font-size: 20px; }
  pre { background: #0A0E1E; border: 1px solid var(--border); padding: 20px; border-radius: 10px; font-size: 18px; line-height: 1.4; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: start; }
  .grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; align-items: start; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 24px; }
  .card-gold { border-color: var(--gold); box-shadow: 0 0 20px rgba(255,204,0,0.2); }
  .pill { display: inline-block; padding: 6px 14px; border-radius: 999px; background: rgba(0,212,255,0.15); color: var(--cyan); font-family: "JetBrains Mono", monospace; font-size: 14px; border: 1px solid rgba(0,212,255,0.3); margin: 4px 4px 4px 0; }
  .pill-gold { background: rgba(255,204,0,0.15); color: var(--gold); border-color: rgba(255,204,0,0.3); }
  .badge { display: inline-block; padding: 8px 18px; border-radius: 999px; background: rgba(230,57,70,0.15); color: var(--crimson); font-family: "JetBrains Mono", monospace; font-size: 12px; letter-spacing: 2px; }
  footer { position: absolute; bottom: 24px; left: 64px; color: var(--dim); font-family: "JetBrains Mono", monospace; font-size: 12px; letter-spacing: 2px; }
---

<!-- _class: "cover lead" -->

<span class="eyebrow">Project 2030 · MyAI Future Hackathon · Track 2 Citizens First</span>

# Arus

<p class="muted" style="font-size:28px; font-style:italic; margin-top: 24px;">arus (BM, n.) — the current of a river; the flow of people, information, and intent</p>

<p class="cyan" style="font-size: 28px; margin-top: 36px; max-width:900px; margin-inline:auto;">
AI that moves Malaysia's rescue faster than any human dispatcher can.
</p>

<span class="badge" style="margin-top: 60px;">SOLO · LIU WEI · 2026-04-21</span>

---

<span class="eyebrow crimson">The cost of uncoordinated rescue</span>

<div class="grid3" style="margin-top: 40px;">
  <div>
    <div class="stat">148,024</div>
    <h3 style="color:#fff">Malaysians displaced</h3>
    <p class="muted">NADMA situation report · Dec 2024 · east-coast monsoon flood</p>
  </div>
  <div>
    <div class="stat gold">100+</div>
    <h3 style="color:#fff">Orang Asli families cut off</h3>
    <p class="muted">Gua Musang interior, after rivers burst — manual relay only.</p>
  </div>
  <div>
    <div class="stat mint">4</div>
    <h3 style="color:#fff">agencies, overlapping zones</h3>
    <p class="muted">BOMBA · NADMA · APM · MMEA — uncoordinated comms during the event.</p>
  </div>
</div>

<p style="font-size:36px; margin-top: 50px; font-style:italic;" class="muted">
"People die waiting for a human to add up the numbers."
</p>

---

<span class="eyebrow">The problem is not courage. It is coordination.</span>

# A dispatcher's job is not doable by humans.

<div class="grid2" style="margin-top: 40px;">
  <div class="card">
    <h3>What a human dispatcher tracks</h3>
    <ul class="muted" style="line-height:1.6; font-size: 22px;">
      <li>5+ rescue assets across 20+ km</li>
      <li>Power / fuel budgets on each</li>
      <li>New triangulated calls every minute</li>
      <li>BM-only briefs for BOMBA, EN-only for NADMA</li>
      <li>Who has already been sent where</li>
    </ul>
  </div>
  <div class="card card-gold">
    <h3 class="gold">What Arus does, in ~18 seconds / cycle</h3>
    <ul style="line-height:1.6; font-size: 22px;">
      <li class="cyan">5-stage Gemini pipeline re-plans every cycle</li>
      <li class="cyan">Power budgets enforced at the tool layer</li>
      <li class="cyan">Live MetMalaysia warnings injected into reasoning</li>
      <li class="cyan">Handoff emitted in BM and EN simultaneously</li>
      <li class="cyan">Firestore audit trail for civil-defence review</li>
    </ul>
  </div>
</div>

---

<span class="eyebrow gold">The technical moat</span>

# MCP — the commander does not know the fleet.

<div class="grid2">
  <div>
    <p style="font-size: 22px;" class="muted">Most agent demos hard-code <code>drone_ids</code>. Arus does not.</p>
    <p style="font-size: 22px;">Gemini calls <code>tools/list_changed</code> every cycle and <em>discovers</em> the current fleet, the available MCP tools, and their live schemas.</p>
    <p style="font-size: 22px;">Add a boat. Remove a drone. Retire a helicopter. <span class="cyan">Arus adapts in the next cycle — zero code change.</span></p>
  </div>
  <div class="card">
    <pre><code>┌─ Gemini 2.5 Flash ─┐
│                    │
│  tools/list_changed ──► MCP server (port 8001)
│                    │         │
│                    │         ├─ discover_fleet
│                    │         ├─ assign_search_mission
│                    │         ├─ list_detections  ⚡ Arus
│                    │         └─ ... 9 total
│                    │
│  Runtime tool bind │
│  + JSON schemas    │
└────────────────────┘</code></pre>
    <p class="muted" style="font-size: 16px; margin-top: 16px;">
      Codebase: <code>backend/services/tool_server.py</code> · 9 tools
    </p>
  </div>
</div>

---

<span class="eyebrow gold">Google ADK · SequentialAgent</span>

# 5 Gemini agents turn chaos into dispatch.

<div class="grid3" style="margin-top: 20px; grid-template-columns: repeat(5, 1fr); gap: 12px;">
  <div class="card" style="padding:16px;">
    <div class="eyebrow">Stage 01</div>
    <h3 class="cyan">Assessor</h3>
    <p class="muted" style="font-size:14px;">Reads fleet, coverage, hotspots, + <span class="gold">MetMalaysia</span></p>
  </div>
  <div class="card" style="padding:16px;">
    <div class="eyebrow">Stage 02</div>
    <h3 class="cyan">Strategist</h3>
    <p class="muted" style="font-size:14px;">Scores targets · power budget · relay plan</p>
  </div>
  <div class="card" style="padding:16px;">
    <div class="eyebrow">Stage 03</div>
    <h3 class="cyan">Dispatcher</h3>
    <p class="muted" style="font-size:14px;">Commits missions · validates power round-trip</p>
  </div>
  <div class="card" style="padding:16px;">
    <div class="eyebrow">Stage 04</div>
    <h3 class="cyan">Analyst</h3>
    <p class="muted" style="font-size:14px;">One-screen SITREP + <code>list_detections</code></p>
  </div>
  <div class="card card-gold" style="padding:16px;">
    <div class="eyebrow">Stage 05</div>
    <h3 class="gold">Agency Dispatcher</h3>
    <p class="muted" style="font-size:14px;">BM/EN handoff → BOMBA / NADMA / APM / MMEA</p>
  </div>
</div>

<p class="muted" style="margin-top: 40px; font-size: 18px;">
  Each stage is a <code>google.adk.agents.LlmAgent</code> with Gemini 2.5 Flash + its own instruction + MCP tool subset. Composed into a <code>SequentialAgent</code>. Session rotation every 15 cycles to avoid context bloat.
</p>

---

<span class="eyebrow">Full Google stack — zero shortcuts</span>

# Every mandated tool, used in its intended role.

<div class="grid2">
  <div>
    <h3 class="cyan">Mandatory</h3>
    <span class="pill">Google Antigravity</span>
    <span class="pill">Google AI Studio</span>
    <span class="pill">Google Cloud Run (asia-southeast1)</span>

    <h3 class="mint" style="margin-top: 30px;">Google AI stack</h3>
    <span class="pill">Gemini 2.5 Flash</span>
    <span class="pill">Google ADK · SequentialAgent</span>
    <span class="pill">Gemini Vision (JSON mode)</span>
  </div>
  <div>
    <h3 class="gold">Google Cloud</h3>
    <span class="pill pill-gold">Firestore (asia-southeast1)</span>
    <span class="pill pill-gold">Artifact Registry</span>
    <span class="pill pill-gold">Secret Manager</span>
    <span class="pill pill-gold">Cloud Build</span>
    <span class="pill pill-gold">IAM + custom SA bindings</span>

    <h3 class="muted" style="margin-top: 30px;">Open protocols</h3>
    <span class="pill">MCP (Model Context Protocol)</span>
    <span class="pill">WebSocket / FastAPI</span>
  </div>
</div>

<p class="muted" style="margin-top: 40px; font-size: 16px;">
  No Codex · no Cursor · no VS Code · no Copilot · no Gemini CLI. Compliance clean.
</p>

---

<span class="eyebrow gold">Malaysia pivot · Stage 5</span>

# A brief BOMBA can act on. In their language.

<div class="grid2">
  <div class="card" style="background:#0A0E1E; border-color: rgba(255,204,0,0.4);">
    <div class="eyebrow gold">Real output · Stage 5 · Cycle 3</div>
<pre style="margin-top: 16px; border: none;"><code>AGENSI: NADMA
KOORDINAT: (5, 9) — Kg. Aring, Gua Musang
KEUTAMAAN: TINGGI
RINGKASAN (BM): Mangsa dikesan di
  kawasan Kg. Aring, Gua Musang.
SUMMARY (EN): Victims detected in
  Kg. Aring area, Gua Musang.
CADANGAN TINDAKAN / RECOMMENDED ACTION:
  Penilaian lanjut dan tindakan
  menyelamat diperlukan.
  Further assessment and rescue
  operations required.</code></pre>
  </div>
  <div>
    <h3 class="gold">Why this wins</h3>
    <ul style="line-height:1.7; font-size: 20px;">
      <li><span class="gold">BM</span> for field teams whose first language is Malay.</li>
      <li><span class="cyan">EN</span> for NADMA coordinators writing federal reports.</li>
      <li><span class="mint">Agency routing</span> — BOMBA for rescue, MMEA for coastal, APM for evacuation, NADMA for coordination.</li>
      <li><span class="crimson">Kampung-level</span> locality (Gua Musang · Kuala Krai · Kota Tinggi · Segamat).</li>
    </ul>
    <p class="muted" style="margin-top: 24px; font-size: 16px;">
      Real kampungs from Dec 2024 flood zones. <br/>
      See <code>backend/core/locality.py</code>.
    </p>
  </div>
</div>

---

<span class="eyebrow">Field feature</span>

# Gemini Vision — photo in, agency out.

<div class="grid2">
  <div>
    <p style="font-size: 22px;" class="muted">A BOMBA team phone uploads a drone frame to:</p>
    <pre><code>POST /api/vision/analyse
  multipart/form-data: file=roof.jpg</code></pre>
    <p style="font-size: 22px; margin-top: 20px;">Gemini 2.5 Flash (JSON mode) returns:</p>
    <ul style="line-height:1.6; font-size: 20px;">
      <li><code>victim_count</code> + <code>severity</code></li>
      <li><code>description_bm</code> + <code>description_en</code></li>
      <li><code>recommended_agency</code></li>
      <li><code>hazards</code> + <code>confidence</code></li>
    </ul>
    <p class="muted" style="margin-top: 20px; font-size: 16px;">
      Non-blocking (<code>asyncio.to_thread</code>) · 429 retry · defensive parse.
    </p>
  </div>
  <div class="card" style="background:#0A0E1E;">
<pre><code>{
  "victim_count": 3,
  "severity": "CRITICAL",
  "description_bm":
    "Tiga individu terperangkap di atas bumbung.",
  "description_en":
    "Three individuals stranded on a roof.",
  "recommended_agency": "BOMBA",
  "hazards": ["fast current", "submerged debris"],
  "confidence": 0.92
}</code></pre>
  </div>
</div>

---

<span class="eyebrow cyan">Malaysia-integrated, not Malaysia-themed</span>

# Live MetMalaysia warnings feed reasoning.

<div class="grid2">
  <div>
    <p style="font-size: 22px;">Arus pulls real warnings from <code>api.data.gov.my/weather/warning</code> every cycle.</p>
    <p style="font-size: 22px; margin-top:20px;">The Assessor sees them as part of its briefing.</p>
    <p style="font-size: 22px; margin-top:20px;">The dashboard surfaces a <span class="crimson">MetMalaysia LIVE</span> badge when warnings are active.</p>
    <ul class="muted" style="line-height:1.5; font-size: 18px; margin-top: 30px;">
      <li>No auth · public government data</li>
      <li>BM + EN both present in payload</li>
      <li>Cached 5 min (<code>backend/services/met_feed.py</code>)</li>
      <li>Graceful degrade if upstream down</li>
    </ul>
  </div>
  <div class="card" style="background:#0A0E1E;">
    <div class="eyebrow crimson">TODAY · 2026-04-20 · 00:30 MYT</div>
<pre style="margin-top: 12px;"><code>warning_issue:
  title_bm: Amaran Ribut Petir
  title_en: Thunderstorms Warning
  issued:   2026-04-20T00:30:00
valid_from:  2026-04-20T01:00:00
valid_to:    2026-04-20T05:00:00

text_en: Thunderstorms, heavy rain and
  strong winds are expected over the
  waters of Perlis & Kedah, Penang,
  East Johor and Pahang...</code></pre>
  </div>
</div>

---

<span class="eyebrow mint">Live demo moment</span>

# Watch the pipeline reason.

<div class="grid2" style="align-items:stretch;">
  <div class="card" style="background:#0A0E1E;">
    <div class="eyebrow cyan">CommandConsole · streaming · cycle 3</div>
<pre style="margin-top: 12px;"><code>[assessor]   tool: get_situation_overview
             → fleet 5/5 · cov 48.8% · hotspot (5,9)
[assessor]   tool: list_detections
             → 4 victims · 2 Gua Musang · 2 Kota Tinggi
[strategist] tool: get_frontier_targets
             → SE quadrant 18.4% — focus here
[strategist] tool: plan_route Bravo → (5,9)
             → 7 cells · 14% · affordable ✓
[dispatcher] tool: assign_search_mission Bravo
             → accepted · ETA 7 ticks
[analyst]    SITREP built · Detections block OK
[agency]     emitted 4 BM/EN handoffs</code></pre>
  </div>
  <div>
    <h3 class="mint">Evidence layer</h3>
    <ul style="line-height:1.7; font-size: 22px;">
      <li><span class="cyan">Every tool call</span> broadcast on WebSocket</li>
      <li><span class="cyan">Every agent reasoning</span> visible to operator</li>
      <li><span class="cyan">No "trust me, it's thinking"</span> opacity</li>
      <li><span class="cyan">Cycle history</span> stored in Firestore</li>
    </ul>
    <p class="muted" style="margin-top: 30px; font-size: 18px;">
      This is how commanders build trust before deployment.
    </p>
  </div>
</div>

---

<span class="eyebrow gold">Malaysian locality model</span>

# A map commanders already know.

<div class="grid2">
  <div>
    <p style="font-size: 22px;">Arus does not report "Sector NE-3".</p>
    <p style="font-size: 22px; margin-top:10px;">Arus reports <span class="gold">Kg. Aring, Gua Musang</span>.</p>
    <p style="font-size: 22px; margin-top:20px;">That matters because:</p>
    <ul style="line-height:1.7; font-size: 20px;">
      <li>Dispatchers already have kampung phone trees</li>
      <li>BOMBA Balai names map 1:1 to districts</li>
      <li>Affected families are identified by kampung, not grid coords</li>
      <li>Post-event NADMA reports are by kampung</li>
    </ul>
  </div>
  <div class="card">
    <h3 class="cyan">Current coverage</h3>
    <span class="pill">Gua Musang, Kelantan</span>
    <span class="pill">Kuala Krai, Kelantan</span>
    <span class="pill pill-gold">Kota Tinggi, Johor</span>
    <span class="pill pill-gold">Segamat, Johor</span>

    <p class="muted" style="margin-top: 24px; font-size: 16px;">
      Demo Day is at UTM Skudai (Johor) — Dec 2024 flood localities are the freshest reference for the judges in the room.
    </p>
    <p class="muted" style="margin-top: 12px; font-size: 16px;">
      Kampung naming deterministic — same grid cell always maps to the same kampung across runs.
    </p>
  </div>
</div>

---

<span class="eyebrow crimson">Impact model</span>

# Minutes become lives.

<div class="grid3" style="margin-top: 40px;">
  <div class="card">
    <div class="big">~45 min</div>
    <h3 style="color:#fff">current dispatch lag</h3>
    <p class="muted" style="font-size:18px;">Manual phone-tree, multi-agency, per remote kampung.</p>
  </div>
  <div class="card card-gold">
    <div class="big mint">~18 sec</div>
    <h3 style="color:#fff">Arus cycle latency</h3>
    <p class="muted" style="font-size:18px;">Full pipeline: MetMalaysia fetch + 5-stage Gemini + MCP dispatch.</p>
  </div>
  <div class="card">
    <div class="big gold">150× faster</div>
    <h3 style="color:#fff">dispatch decision loop</h3>
    <p class="muted" style="font-size:18px;">Each saved minute in flood water is ~2-4 % survival-probability uplift.</p>
  </div>
</div>

<p class="muted" style="margin-top: 40px; font-size: 20px;">
  Assumptions published in <code>docs/impact-model.md</code>. <br/>
  Source: DOSM mortality tables · MERCY Malaysia SAR reports · peer-reviewed swift-water survival studies.
</p>

---

<span class="eyebrow">Scale path</span>

# Same codebase, new geographies.

<div class="grid3" style="margin-top: 30px;">
  <div class="card">
    <h3 class="cyan">Now</h3>
    <p style="font-size: 18px;">Peninsula east-coast monsoon belt · Kelantan + Johor.</p>
    <ul class="muted" style="font-size:15px;"><li>4 districts</li><li>16 kampungs</li></ul>
  </div>
  <div class="card">
    <h3 class="mint">+1 week</h3>
    <p style="font-size: 18px;">Sabah (Beaufort, Papar) + Sarawak (Kapit, Mukah) river floods.</p>
    <ul class="muted" style="font-size:15px;"><li>Swap <code>locality.py</code></li><li>Add MMEA maritime</li></ul>
  </div>
  <div class="card card-gold">
    <h3 class="gold">+1 month</h3>
    <p style="font-size: 18px;">ASEAN monsoon belt · Philippines typhoons, Vietnam Mekong floods, Thailand Chao Phraya.</p>
    <ul class="muted" style="font-size:15px;"><li>Gemini already multilingual</li><li>Agency dispatcher swap only</li></ul>
  </div>
</div>

<p class="muted" style="margin-top: 40px; font-size: 20px;">
  Core pipeline is region-agnostic. Only the <span class="gold">Agency Dispatcher</span> and <code>locality.py</code> ever need local tuning.
</p>

---

<span class="eyebrow gold">National alignment</span>

# Arus speaks Kerajaan's language.

<div class="grid2">
  <div>
    <h3 class="cyan">Malaysia Madani</h3>
    <p style="font-size: 20px;" class="muted">Digital-transformation of public safety is a cited priority. Arus is agency-collaborative by design.</p>

    <h3 class="cyan" style="margin-top: 30px;">MyDIGITAL</h3>
    <p style="font-size: 20px;" class="muted">"AI for the Rakyat" — Arus applies frontier AI to a mass-market public-safety problem, not enterprise productivity.</p>

    <h3 class="cyan" style="margin-top: 30px;">AI Nation 2030</h3>
    <p style="font-size: 20px;" class="muted">Demonstrates Malaysian builders shipping production agentic systems on the Google stack, in Malaysia's language.</p>
  </div>
  <div>
    <h3 class="gold">GovTech Malaysia Unit</h3>
    <ul style="line-height:1.7; font-size: 20px;">
      <li>Multi-agency workflow</li>
      <li>Bilingual by default</li>
      <li>Firestore-backed audit log (§ records retention)</li>
      <li>Cloud Run sovereign region (<code>asia-southeast1</code>)</li>
      <li>Zero vendor lock beyond Google AI</li>
      <li>Open-source (MIT)</li>
    </ul>
    <p class="muted" style="margin-top: 30px; font-size: 18px;">
      Ready to hand to BOMBA digital ops as a starting point — not a research demo.
    </p>
  </div>
</div>

---

<!-- _class: "cover" -->

<h1 style="font-size: 180px; letter-spacing: -4px;">Arus</h1>

<p class="cyan" style="font-size: 32px; margin-top: 24px;">
AI that moves Malaysia's rescue — faster than any human dispatcher can.
</p>

<div style="margin-top: 50px;">
  <span class="pill" style="font-size: 18px;">github.com/SunflowersLwtech/arus</span>
  <span class="pill pill-gold" style="font-size: 18px;">arus-1030181742799.asia-southeast1.run.app</span>
</div>

<p class="muted" style="margin-top: 60px; font-size: 18px;">
  Built solo by <span class="cyan">Liu Wei</span> · Project 2030 · MyAI Future Hackathon · Track 2 · 2026-04-21
</p>

<p class="muted" style="margin-top: 40px; font-size: 16px;">
  Terima kasih. Thank you. 谢谢.
</p>
