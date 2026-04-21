import useMissionStore from '../stores/missionStore'

// Sim runs at ~5 Hz → 1 tick ≈ 0.2 s
const TICKS_PER_SECOND = 5

export default function NextCallEta() {
  const nextTick = useMissionStore(s => s.nextCardTick)
  const currentTick = useMissionStore(s => s.currentTick)
  const currentCard = useMissionStore(s => s.currentCard)
  const targetingDroneId = useMissionStore(s => s.targetingDroneId)
  const locale = useMissionStore(s => s.locale)

  if (targetingDroneId) {
    return (
      <div className="absolute top-3 right-3 z-20 px-3 py-1.5 rounded-full text-[11px] font-mono font-semibold shadow-lg"
        style={{ background: '#FFCC00', color: '#0B1426' }}>
        🎯 {locale === 'bm' ? 'Klik peta untuk hantar' : 'Click the map to dispatch'}
      </div>
    )
  }

  if (currentCard || nextTick == null) return null

  const remaining = Math.max(0, nextTick - currentTick)
  const seconds = Math.ceil(remaining / TICKS_PER_SECOND)

  return (
    <div className="absolute top-3 right-3 z-20 px-3 py-1.5 rounded-full text-[11px] font-mono shadow-lg"
      style={{ background: 'rgba(0,212,255,0.15)', color: '#00D4FF', border: '1px solid rgba(0,212,255,0.4)' }}>
      📞 {locale === 'bm' ? `Panggilan seterusnya ~${seconds}s` : `Next call ~${seconds}s`}
    </div>
  )
}
