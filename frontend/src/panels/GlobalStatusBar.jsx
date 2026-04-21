import { useEffect, useState } from 'react'
import useMissionStore from '../stores/missionStore'
import LanguageToggle from '../components/LanguageToggle'

const STATUS_LABELS = {
  idle: 'Ready',
  running: 'In Progress',
  paused: 'Paused',
  completed: 'Complete',
}
const STATUS_COLORS = {
  idle: '#6C757D',
  running: '#06D6A0',
  paused: '#F4A261',
  completed: '#00D4FF',
}

export default function GlobalStatusBar() {
  const missionStatus = useMissionStore(s => s.missionStatus)
  const tick = useMissionStore(s => s.tick)
  const fleet = useMissionStore(s => s.fleet)
  const coverage = useMissionStore(s => s.coverage)
  const objectivesFound = useMissionStore(s => s.objectivesFound)
  const objectivesTotal = useMissionStore(s => s.objectivesTotal)
  const connected = useMissionStore(s => s.connected)

  // MetMalaysia live-feed indicator (polls every 5 min, same TTL as backend cache)
  const [metCount, setMetCount] = useState(null)
  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const r = await fetch('/api/live/warnings')
        if (!r.ok) throw new Error('bad')
        const j = await r.json()
        if (!cancelled) setMetCount(typeof j?.count === 'number' ? j.count : 0)
      } catch {
        if (!cancelled) setMetCount(null)
      }
    }
    load()
    const id = setInterval(load, 5 * 60 * 1000)
    return () => { cancelled = true; clearInterval(id) }
  }, [])

  const activeCount = fleet.filter(u => u.status !== 'offline').length
  const avgPower = fleet.length > 0
    ? Math.round(fleet.reduce((s, u) => s + u.power, 0) / fleet.length)
    : 0

  const mm = String(Math.floor(tick / 60)).padStart(2, '0')
  const ss = String(tick % 60).padStart(2, '0')

  const statusColor = STATUS_COLORS[missionStatus] || '#6C757D'

  return (
    <div className="flex items-center justify-between px-4 py-2 border-b"
      style={{ background: '#111B2E', borderColor: '#1E3A5F' }}>

      {/* Left: Identity & mission status */}
      <div className="flex items-center gap-4">
        <span className="font-mono text-sm font-bold" style={{ color: '#00D4FF' }}>
          ARUS
        </span>
        <span className="font-mono text-[10px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
          Malaysia Flood Command · Kelantan + Johor Belt
        </span>

        <div className="flex items-center gap-2 px-2.5 py-0.5 rounded"
          style={{ background: `${statusColor}15`, border: `1px solid ${statusColor}40` }}>
          <span className={`inline-block w-2 h-2 rounded-full ${missionStatus === 'running' ? 'animate-pulse' : ''}`}
            style={{ background: statusColor }} />
          <span className="font-mono text-xs font-semibold" style={{ color: statusColor }}>
            {STATUS_LABELS[missionStatus] || missionStatus}
          </span>
        </div>

        <span className="font-mono text-sm tabular-nums" style={{ color: 'rgba(255,255,255,0.7)' }}>
          {mm}:{ss}
        </span>
      </div>

      {/* Right: Key metrics */}
      <div className="flex items-center gap-1">
        {/* Fleet */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded cursor-help"
          style={{ background: 'rgba(6,214,160,0.08)' }}
          title={`Unmanned aerial vehicles online — ${activeCount} of ${fleet.length} drones active, average battery ${avgPower}%. Drones fly rescue missions when you pick a dispatch option.`}>
          <span className="text-[10px] font-mono" style={{ color: 'rgba(255,255,255,0.4)' }}>UAV</span>
          <span className="font-mono text-xs font-bold" style={{ color: '#06D6A0' }}>
            {activeCount}/{fleet.length}
          </span>
          <span className="text-[10px] font-mono" style={{ color: 'rgba(255,255,255,0.3)' }}>
            {avgPower}%
          </span>
        </div>

        {/* Coverage */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded cursor-help"
          style={{ background: 'rgba(0,212,255,0.08)' }}
          title={`Coverage — percentage of the 20×20 flood grid scanned so far (${coverage.toFixed(1)}%). Higher coverage = fewer blind spots.`}>
          <span className="text-[10px] font-mono" style={{ color: 'rgba(255,255,255,0.4)' }}>COV</span>
          <span className="font-mono text-xs font-bold" style={{ color: '#00D4FF' }}>
            {coverage.toFixed(1)}%
          </span>
        </div>

        {/* Objectives */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded cursor-help"
          style={{ background: objectivesFound > 0 ? 'rgba(6,214,160,0.08)' : 'rgba(244,162,97,0.08)' }}
          title={`Objectives — victim detection markers on the map (${objectivesFound} found of ${objectivesTotal} total).`}>
          <span className="text-[10px] font-mono" style={{ color: 'rgba(255,255,255,0.4)' }}>OBJ</span>
          <span className="font-mono text-xs font-bold"
            style={{ color: objectivesFound >= objectivesTotal && objectivesTotal > 0 ? '#06D6A0' : '#F4A261' }}>
            {objectivesFound}/{objectivesTotal}
          </span>
        </div>

        {/* MetMalaysia LIVE badge — proof of Malaysia integration */}
        {metCount !== null && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded"
            style={{ background: metCount > 0 ? 'rgba(230,57,70,0.15)' : 'rgba(6,214,160,0.08)' }}
            title={metCount > 0
              ? `${metCount} active MetMalaysia warnings — feeding into the Assessor agent this cycle`
              : 'MetMalaysia feed live · no active warnings'}>
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${metCount > 0 ? 'animate-pulse' : ''}`}
              style={{ background: metCount > 0 ? '#E63946' : '#06D6A0' }} />
            <span className="font-mono text-[10px] font-semibold"
              style={{ color: metCount > 0 ? '#E63946' : '#06D6A0', letterSpacing: 1.5 }}>
              METMY {metCount > 0 ? `LIVE ×${metCount}` : 'CLEAR'}
            </span>
          </div>
        )}

        {/* Connection */}
        <div className="flex items-center gap-1 px-2 py-1">
          <span className={`inline-block w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-400' : 'bg-red-500 animate-pulse'}`} />
          <span className="font-mono text-[10px]" style={{ color: 'rgba(255,255,255,0.4)' }}>
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>

        {/* BM/EN toggle — live during play */}
        <LanguageToggle />
      </div>
    </div>
  )
}
