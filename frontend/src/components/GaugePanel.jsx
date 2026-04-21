import useMissionStore from '../stores/missionStore'

function formatTime(seconds) {
  const s = Math.max(0, Math.floor(seconds))
  const m = Math.floor(s / 60)
  const r = s % 60
  return `${m}:${r.toString().padStart(2, '0')}`
}

function Bar({ label, value, max, tone, trailing, hint }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  const color = tone === 'danger' ? '#FF4F5E' : tone === 'warn' ? '#FFB84D' : '#00D4FF'
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] uppercase tracking-widest" style={{ color: '#7A8BA3' }}>{label}</span>
        <span className="text-sm font-mono font-semibold text-white">{trailing ?? value}</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#1E3A5F' }}>
        <div className="h-full transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
      </div>
      {hint && (
        <div className="text-[9px] mt-0.5" style={{ color: '#7A8BA3' }}>{hint}</div>
      )}
    </div>
  )
}

export default function GaugePanel() {
  const gauges = useMissionStore(s => s.gauges)
  const scenario = useMissionStore(s => s.scenario)
  const locale = useMissionStore(s => s.locale)
  const mode = useMissionStore(s => s.mode)
  const target = scenario?.target_saved ?? 14
  const duration = scenario?.duration_seconds ?? 420

  const labels = locale === 'bm'
    ? { saved: 'Diselamatkan', assets: 'Aset', trust: 'Kepercayaan', time: 'Masa' }
    : { saved: 'Lives saved', assets: 'Assets', trust: 'Trust', time: 'Time left' }

  // Per-mode context under the time bar — judge feedback: "players don't
  // know what running out of time means in COACH/AUTO modes."
  const timeHint = locale === 'bm'
    ? (mode === 'COACH' ? 'Pada 0:00 → ringkasan misi' : mode === 'AUTO' ? 'AI urus masa' : 'Pada 0:00 → ringkasan misi')
    : (mode === 'COACH' ? 'at 0:00 → mission debrief' : mode === 'AUTO' ? 'AI paces the clock' : 'at 0:00 → mission debrief')

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4">
      <Bar
        label={labels.saved}
        value={gauges.saved}
        max={target}
        tone={gauges.saved >= target * 0.6 ? 'ok' : 'warn'}
        trailing={`${gauges.saved} / ${target}`}
      />
      <Bar
        label={labels.assets}
        value={gauges.assets}
        max={100}
        tone={gauges.assets < 20 ? 'danger' : gauges.assets < 50 ? 'warn' : 'ok'}
        trailing={`${Math.round(gauges.assets)}%`}
      />
      <Bar
        label={labels.trust}
        value={gauges.trust}
        max={100}
        tone={gauges.trust < 30 ? 'danger' : gauges.trust < 60 ? 'warn' : 'ok'}
        trailing={`${Math.round(gauges.trust)}%`}
      />
      <Bar
        label={labels.time}
        value={gauges.time_remaining}
        max={duration}
        tone={gauges.time_remaining < 60 ? 'danger' : gauges.time_remaining < 180 ? 'warn' : 'ok'}
        trailing={formatTime(gauges.time_remaining)}
        hint={timeHint}
      />
    </div>
  )
}
