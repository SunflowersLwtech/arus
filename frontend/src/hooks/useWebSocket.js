/**
 * Module-level WebSocket singleton — immune to React StrictMode.
 *
 * Handles inbound state_update / game_card / player_command_result / game_over
 * messages from the backend simulation loop. Game commands themselves go
 * via REST (see hooks/useGameApi.js), not WS.
 */
import { useEffect } from 'react'
import useMissionStore from '../stores/missionStore'

const WS_PROTO = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const WS_URL = `${WS_PROTO}//${window.location.host}/ws/live`
const MAX_ATTEMPTS = 10

let ws = null
let attempt = 0
let timer = null

function handleMessage(event) {
  try {
    const msg = JSON.parse(event.data)
    const store = useMissionStore.getState()

    if (msg.type === 'state_update' || msg.type === 'initial_state') {
      store.updateState(msg.payload)
      if (msg.game !== undefined) store.applyGameSnapshot(msg.game)
      if (msg.mode && msg.mode !== store.mode) {
        // server-authoritative mode (rare — happens if start mutated it)
      }
      if (msg.payload?.flooded_cells) store.setFloodedCells(msg.payload.flooded_cells)
    } else if (msg.type === 'game_card') {
      store.presentCard(msg.payload)
      // When the card finally surfaces, clear its pre-alert marker.
      if (msg.payload?.id) store.clearPreAlert(msg.payload.id)
    } else if (msg.type === 'prealert') {
      store.addPreAlert(msg.payload)
    } else if (msg.type === 'agency_handoff') {
      store.setLatestHandoff({ ...msg.payload, ts: Date.now() })
    } else if (msg.type === 'player_command_result') {
      if (msg.payload?.ok) store.applyChoiceResult(msg.payload)
    } else if (msg.type === 'game_over') {
      store.setGameOver(msg.payload)
    } else if (msg.type === 'narrator_log') {
      store.pushNarratorLog(msg.payload)
    } else if (msg.type === 'agent_log') {
      store.pushCoachLog(msg.payload)
    } else if (msg.type === 'agent_status') {
      store.setAutoStatus(msg.payload)
    } else if (msg.type === 'coach_recommendation') {
      store.setRecommendation(msg.payload)
    }
  } catch (e) {
    console.error('[WS] Parse error:', e)
  }
}

function connect() {
  if (ws && ws.readyState !== WebSocket.CLOSED) return

  ws = new WebSocket(WS_URL)

  ws.onopen = () => {
    useMissionStore.getState().setConnected(true)
    attempt = 0
    console.log('[WS] Connected')
  }

  ws.onmessage = handleMessage

  ws.onerror = (err) => {
    console.error('[WS] Connection error:', err)
  }

  ws.onclose = () => {
    useMissionStore.getState().setConnected(false)
    ws = null
    if (attempt < MAX_ATTEMPTS) {
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000)
      attempt += 1
      console.log(`[WS] Reconnecting in ${delay}ms (attempt ${attempt})`)
      timer = setTimeout(connect, delay)
    }
  }
}

setTimeout(connect, 100)

export default function useWebSocket() {
  useEffect(() => {
    if (!ws || ws.readyState === WebSocket.CLOSED) {
      attempt = 0
      clearTimeout(timer)
      connect()
    }
  }, [])
  return {}
}
