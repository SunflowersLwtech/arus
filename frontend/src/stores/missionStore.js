import { create } from 'zustand'

const useMissionStore = create((set, get) => ({
  // ─── World state (R3F scene) ─────────────────────────────
  fleet: [],
  coverage: 0,
  objectives: [],
  exploredGrid: [],
  obstacles: [],
  heatmap: [],
  hotspots: [],
  gridSize: 20,
  base: [0, 0],
  missionStatus: 'idle',
  tick: 0,
  objectivesFound: 0,
  objectivesTotal: 0,
  events: [],

  // ─── Game state (Banjir Drill) ───────────────────────────
  locale: 'en',                     // 'en' | 'bm'
  gameStatus: 'not_started',        // not_started | running | won | partial | failed
  gameStatusReason: '',
  scenario: null,                   // {id, name_en, name_bm, target_saved, duration_seconds, intro_hook_en/bm}
  gauges: { saved: 0, assets: 100, trust: 100, time_remaining: 0 },
  currentCard: null,                // {id, title_en, title_bm, body_*, options: [{id, label_en, label_bm}]}
  narratorLog: [],                  // [{id, timestamp, speaker, text_en, text_bm, tone}]
  choiceHistory: [],
  debrief: null,                    // populated when game over
  nextCardTick: null,               // tick at which next scheduled card will appear
  currentTick: 0,                   // from game engine snapshot
  targetingDroneId: null,           // when set, map click dispatches this drone

  // ─── Connection ─────────────────────────────────────────
  connected: false,

  // ─── Actions ────────────────────────────────────────────
  updateState: (payload) => set(state => ({
    fleet: payload.fleet || state.fleet,
    coverage: payload.coverage_pct ?? state.coverage,
    objectives: payload.objectives || state.objectives,
    exploredGrid: payload.explored || state.exploredGrid,
    obstacles: payload.obstacles || state.obstacles,
    heatmap: payload.heatmap || state.heatmap,
    hotspots: payload.hotspots || state.hotspots,
    gridSize: payload.grid_size || state.gridSize,
    base: payload.base || state.base,
    missionStatus: payload.mission_status || state.missionStatus,
    tick: payload.tick ?? state.tick,
    objectivesFound: payload.objectives_found ?? state.objectivesFound,
    objectivesTotal: payload.objectives_total ?? state.objectivesTotal,
    events: payload.events || state.events,
  })),

  applyGameSnapshot: (g) => set(state => {
    if (!g) return {}
    // Client-authoritative: once the user is on the Start screen we
    // ignore server snapshots entirely (avoids hijacking visitors into a
    // previous player's session on a single-instance Cloud Run).
    if (state.gameStatus === 'not_started') return {}
    return {
      scenario: g.scenario ?? state.scenario,
      gauges: g.gauges ?? state.gauges,
      gameStatus: g.status ?? state.gameStatus,
      gameStatusReason: g.status_reason ?? state.gameStatusReason,
      currentCard: g.current_card ?? state.currentCard,
      choiceHistory: g.history ?? state.choiceHistory,
      // locale is owned by the client — never let the server's initial
      // locale overwrite the user's BM/EN toggle.
      nextCardTick: g.next_card_tick ?? state.nextCardTick,
      currentTick: g.tick ?? state.currentTick,
    }
  }),

  setTargetingDroneId: (id) => set({ targetingDroneId: id }),

  pushNarratorLog: (entry) => set(state => ({
    narratorLog: [
      ...state.narratorLog.slice(-40),
      { timestamp: Date.now(), ...entry },
    ],
  })),

  startGameLocal: ({ session_id, scenario, gauges, intro }) => set({
    gameStatus: 'running',
    gameStatusReason: '',
    scenario,
    gauges,
    currentCard: null,
    narratorLog: [{
      id: 'intro',
      timestamp: Date.now(),
      speaker: 'NADMA · Datuk Nadia',
      text_en: intro?.en || scenario.intro_hook_en || '',
      text_bm: intro?.bm || scenario.intro_hook_bm || '',
      tone: 'intro',
    }],
    choiceHistory: [],
    debrief: null,
  }),

  presentCard: (card) => set({ currentCard: card }),

  applyChoiceResult: ({ card_id, option_id, flavor, gauges, deltas }) => set(state => {
    const resolved = state.currentCard
    const base = Date.now()

    const summaryParts = { en: [], bm: [] }
    if (deltas?.saved) {
      const s = deltas.saved > 0 ? `+${deltas.saved}` : `${deltas.saved}`
      summaryParts.en.push(`${s} lives`)
      summaryParts.bm.push(`${s} nyawa`)
    }
    if (deltas?.assets) {
      const s = deltas.assets > 0 ? `+${deltas.assets}` : `${deltas.assets}`
      summaryParts.en.push(`${s}% assets`)
      summaryParts.bm.push(`${s}% aset`)
    }
    if (deltas?.trust) {
      const s = deltas.trust > 0 ? `+${deltas.trust}` : `${deltas.trust}`
      summaryParts.en.push(`${s}% trust`)
      summaryParts.bm.push(`${s}% kepercayaan`)
    }
    const summaryEn = summaryParts.en.length ? `⚙️  ${summaryParts.en.join(' · ')}` : ''
    const summaryBm = summaryParts.bm.length ? `⚙️  ${summaryParts.bm.join(' · ')}` : ''

    const flavorEntry = {
      id: `${card_id}-${option_id}-${base}`,
      timestamp: base,
      speaker: resolved ? (resolved.title_en || card_id) : card_id,
      text_en: flavor?.en || '',
      text_bm: flavor?.bm || '',
      tone: 'choice_result',
    }
    const systemEntry = summaryEn || summaryBm ? [{
      id: `${card_id}-${option_id}-sys-${base}`,
      timestamp: base + 1,
      speaker: 'Dispatcher log',
      text_en: summaryEn,
      text_bm: summaryBm,
      tone: 'system',
    }] : []

    return {
      gauges: gauges ?? state.gauges,
      currentCard: null,
      choiceHistory: [...state.choiceHistory, { card_id, option_id, flavor, deltas }],
      narratorLog: [
        ...state.narratorLog.slice(-30),
        flavorEntry,
        ...systemEntry,
      ],
    }
  }),

  setGameOver: ({ status, reason, gauges }) => set(state => ({
    gameStatus: status,
    gameStatusReason: reason,
    gauges: gauges ?? state.gauges,
    currentCard: null,
  })),

  setDebrief: (debrief) => set({ debrief }),

  setLocale: (locale) => set({ locale }),

  setConnected: (val) => set({ connected: val }),

  resetGame: () => set({
    gameStatus: 'not_started',
    gameStatusReason: '',
    scenario: null,
    gauges: { saved: 0, assets: 100, trust: 100, time_remaining: 0 },
    currentCard: null,
    narratorLog: [],
    choiceHistory: [],
    debrief: null,
  }),
}))

export default useMissionStore
