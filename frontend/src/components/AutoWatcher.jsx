import { useEffect, useRef } from 'react'
import useMissionStore from '../stores/missionStore'

// Stage ordering matches the 5-stage SequentialAgent in
// backend/agents/auto_commander.py
const STAGES = [
  { id: 'assessor',          en: 'Assess',     bm: 'Nilai',      color: '#00D4FF' },
  { id: 'strategist',        en: 'Strategise', bm: 'Strategi',   color: '#4DA8DA' },
  { id: 'dispatcher',        en: 'Dispatch',   bm: 'Hantar',     color: '#06D6A0' },
  { id: 'analyst',           en: 'Analyse',    bm: 'Analisis',   color: '#FFCC00' },
  { id: 'agency_dispatcher', en: 'BM/EN Brief',bm: 'Taklimat',   color: '#FF6A3D' },
]

function StageBar({ activeAgent, locale }) {
  return (
    <div className="grid grid-cols-5 gap-1 px-2 py-2 border-b" style={{ borderColor: '#1E3A5F' }}>
      {STAGES.map(s => {
        const active = activeAgent === s.id
        return (
          <div
            key={s.id}
            className="text-center px-1 py-1.5 rounded text-[9px] font-mono"
            style={{
              background: active ? `${s.color}30` : '#0B1426',
              border: `1px solid ${active ? s.color : '#1E3A5F'}`,
              color: active ? s.color : '#7A8BA3',
            }}
          >
            {locale === 'bm' ? s.bm : s.en}
          </div>
        )
      })}
    </div>
  )
}

function AutoLogEntry({ entry, locale }) {
  const stage = STAGES.find(s => s.id === entry.agent)
  const color = stage?.color || '#9EB0C8'
  const k = entry.kind
  if (k === 'tool_call') {
    const argsStr = Object.entries(entry.args || {}).map(([k, v]) => `${k}=${v}`).join(', ')
    return (
      <div className="text-[11px] font-mono px-2 py-1 mb-1 rounded"
        style={{ background: `${color}10`, borderLeft: `2px solid ${color}` }}>
        <span style={{ color }}>⚙ {entry.agent}</span>
        <span style={{ color: '#9EB0C8' }}> · {entry.tool}({argsStr})</span>
      </div>
    )
  }
  if (k === 'tool_result') {
    return (
      <div className="text-[11px] font-mono px-2 py-1 mb-1 rounded"
        style={{ background: `${color}10`, borderLeft: `2px solid ${color}` }}>
        <span style={{ color }}>↳ {entry.tool}</span>
        <span style={{ color: '#9EB0C8' }}> · {(entry.result || '').slice(0, 120)}</span>
      </div>
    )
  }
  return (
    <div className="mb-2">
      <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color }}>
        {entry.agent}
      </div>
      <div className="text-[12px] leading-relaxed whitespace-pre-wrap" style={{ color: '#E6F0FA' }}>
        {(entry.text || '').slice(0, 600)}
      </div>
    </div>
  )
}

export default function AutoWatcher() {
  const autoLog = useMissionStore(s => s.autoLog)
  const autoStatus = useMissionStore(s => s.autoStatus)
  const locale = useMissionStore(s => s.locale)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [autoLog])

  // Active agent = the agent of the most recent log entry, or the first stage if none yet
  const activeAgent = autoLog.length > 0 ? autoLog[autoLog.length - 1].agent : null
  const latestStatus = autoStatus?.status || 'idle'

  return (
    <div className="h-full flex flex-col" style={{ background: '#0F1C33' }}>
      <div className="px-3 py-2 border-b" style={{ borderColor: '#1E3A5F' }}>
        <div className="text-[10px] uppercase tracking-widest" style={{ color: '#FF6A3D' }}>
          🎛 {locale === 'bm' ? 'AUTO · ADK 5-peringkat' : 'AUTO · 5-stage ADK pipeline'}
        </div>
        <div className="text-[9px] mt-0.5 font-mono" style={{ color: '#7A8BA3' }}>
          status: <span style={{ color: latestStatus === 'thinking' ? '#FFCC00' : latestStatus === 'error' ? '#FF5E78' : '#06D6A0' }}>
            {latestStatus}
          </span>
          {autoStatus?.cycle != null && ` · cycle ${autoStatus.cycle}`}
          {autoStatus?.elapsed != null && ` · ${autoStatus.elapsed}s`}
        </div>
      </div>
      <StageBar activeAgent={activeAgent} locale={locale} />
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3">
        {autoLog.length === 0 && (
          <div className="text-xs italic" style={{ color: '#7A8BA3' }}>
            {locale === 'bm'
              ? 'Menunggu kitaran AUTO pertama (~5s).'
              : 'Waiting for first AUTO cycle (~5s).'}
          </div>
        )}
        {autoLog.map(entry => <AutoLogEntry key={entry.id} entry={entry} locale={locale} />)}
      </div>
    </div>
  )
}
