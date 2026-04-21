/** REST helpers for /api/game/* endpoints. */
import useMissionStore from '../stores/missionStore'

async function postJson(url, body) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : '{}',
  })
  if (!resp.ok) throw new Error(`${url} → HTTP ${resp.status}`)
  return resp.json()
}

async function getJson(url) {
  const resp = await fetch(url)
  if (!resp.ok) throw new Error(`${url} → HTTP ${resp.status}`)
  return resp.json()
}

export async function startGame(scenarioId = 'shah_alam_hard', locale = 'en', mode = 'PLAY') {
  const { data } = await postJson('/api/game/start', { scenario_id: scenarioId, locale, mode })
  const store = useMissionStore.getState()
  store.setMode(data.mode || mode)
  store.setLocale(locale)
  if ((data.mode || mode) === 'AUTO') {
    // AUTO has no scenario/gauges — flip gameStatus manually so UI leaves Start
    store.setRecommendation(null)
    useMissionStore.setState({
      gameStatus: 'running',
      debrief: null,
      coachLog: [],
      autoLog: [],
      narratorLog: [{
        id: 'auto-intro',
        timestamp: Date.now(),
        speaker: 'Arus · AUTO mode',
        text_en: 'Commander pipeline engaged. Watching the AI dispatch autonomously.',
        text_bm: 'Barisan arahan aktif. Perhatikan AI menghantar secara autonomi.',
        tone: 'intro',
      }],
      choiceHistory: [],
    })
  } else {
    store.startGameLocal(data)
  }
  // Stash today's live MetMalaysia warnings so the Start/Debrief can
  // surface "same URL, different day, different drill".
  store.setLiveWarnings(data.live_warnings || [])
  return data
}

export async function chooseOption(cardId, optionId) {
  const { data } = await postJson('/api/game/choose', { card_id: cardId, option_id: optionId })
  if (data?.ok) {
    useMissionStore.getState().applyChoiceResult({
      card_id: data.card_id,
      option_id: data.option_id,
      flavor: data.flavor,
      gauges: data.gauges,
      deltas: data.deltas,
    })
  }
  return data
}

export async function fetchDebrief() {
  const { data } = await getJson('/api/game/debrief')
  useMissionStore.getState().setDebrief(data)
  return data
}

export async function manualDispatch(droneId, x, y) {
  const { data } = await postJson('/api/game/dispatch', { drone_id: droneId, x, y })
  return data
}
