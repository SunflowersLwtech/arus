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
    return {
      scenario: g.scenario ?? state.scenario,
      gauges: g.gauges ?? state.gauges,
      gameStatus: g.status ?? state.gameStatus,
      gameStatusReason: g.status_reason ?? state.gameStatusReason,
      currentCard: g.current_card ?? state.currentCard,
      choiceHistory: g.history ?? state.choiceHistory,
      locale: g.locale ?? state.locale,
    }
  }),

  startGameLocal: ({ session_id, scenario, gauges }) => set({
    gameStatus: 'running',
    gameStatusReason: '',
    scenario,
    gauges,
    currentCard: null,
    narratorLog: [{
      id: 'intro',
      timestamp: Date.now(),
      speaker: 'NADMA',
      text_en: scenario.intro_hook_en || '',
      text_bm: scenario.intro_hook_bm || '',
      tone: 'intro',
    }],
    choiceHistory: [],
    debrief: null,
  }),

  presentCard: (card) => set({ currentCard: card }),

  applyChoiceResult: ({ card_id, option_id, flavor, gauges }) => set(state => {
    const resolved = state.currentCard
    return {
      gauges: gauges ?? state.gauges,
      currentCard: null,
      choiceHistory: [...state.choiceHistory, { card_id, option_id, flavor }],
      narratorLog: [
        ...state.narratorLog.slice(-30),
        {
          id: `${card_id}-${option_id}-${Date.now()}`,
          timestamp: Date.now(),
          speaker: resolved ? (resolved.title_en || card_id) : card_id,
          text_en: flavor?.en || '',
          text_bm: flavor?.bm || '',
          tone: 'choice_result',
        },
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
