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

export async function startGame(scenarioId = 'shah_alam_hard', locale = 'en') {
  const { data } = await postJson('/api/game/start', { scenario_id: scenarioId, locale })
  useMissionStore.getState().startGameLocal(data)
  useMissionStore.getState().setLocale(locale)
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
    })
  }
  return data
}

export async function fetchDebrief() {
  const { data } = await getJson('/api/game/debrief')
  useMissionStore.getState().setDebrief(data)
  return data
}
