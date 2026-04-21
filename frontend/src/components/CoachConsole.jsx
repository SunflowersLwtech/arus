import { useEffect, useRef } from 'react'
import useMissionStore from '../stores/missionStore'

const KIND_STYLE = {
  reasoning: { color: '#00D4FF', label_en: 'reasoning', label_bm: 'pemikiran' },
  tool_call: { color: '#FFCC00', label_en: 'tool', label_bm: 'alat' },
  tool_result: { color: '#06D6A0', label_en: 'result', label_bm: 'hasil' },
}

function LogEntry({ entry, locale }) {
  const k = entry.kind || 'reasoning'
  const style = KIND_STYLE[k] || KIND_STYLE.reasoning
  const labels = locale === 'bm'
    ? { label: style.label_bm, stage: entry.agent || 'coach' }
    : { label: style.label_en, stage: entry.agent || 'coach' }

  if (k === 'tool_call') {
    const argsStr = Object.entries(entry.args || {}).map(([k, v]) => `${k}=${v}`).join(', ')
    return (
      <div className="text-[11px] font-mono px-2 py-1 mb-1.5 rounded"
        style={{ background: `${style.color}10`, borderLeft: `2px solid ${style.color}` }}>
        <span style={{ color: style.color }}>⚙️ {entry.agent}</span>
        <span style={{ color: '#9EB0C8' }}> · {entry.tool}({argsStr})</span>
      </div>
    )
  }
  if (k === 'tool_result') {
    return (
      <div className="text-[11px] font-mono px-2 py-1 mb-1.5 rounded"
        style={{ background: `${style.color}10`, borderLeft: `2px solid ${style.color}` }}>
        <span style={{ color: style.color }}>↳ {entry.tool}</span>
        <span style={{ color: '#9EB0C8' }}> · {(entry.result || '').slice(0, 140)}</span>
      </div>
    )
  }
  // reasoning
  const text = entry.text || ''
  return (
    <div className="mb-2">
      <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: style.color }}>
        {labels.stage} · {labels.label}
      </div>
      <div className="text-[12px] leading-relaxed whitespace-pre-wrap" style={{ color: '#E6F0FA' }}>
        {text}
      </div>
    </div>
  )
}

function RecommendationCard({ rec, locale, currentCard }) {
  if (!rec) return null
  // Only show when it matches the current card (avoid stale recs from prior card)
  if (currentCard && rec.card_id && rec.card_id !== currentCard.id) return null

  const reasoning = locale === 'bm'
    ? (rec.reasoning_bm || rec.reasoning_en)
    : (rec.reasoning_en || rec.reasoning_bm)

  const confidenceColor = rec.confidence === 'high' ? '#06D6A0'
    : rec.confidence === 'low' ? '#FF5E78' : '#FFCC00'

  return (
    <div className="shrink-0 p-3 border-t" style={{ borderColor: '#FFCC0040', background: 'rgba(255,204,0,0.06)' }}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="text-[10px] uppercase tracking-widest" style={{ color: '#FFCC00' }}>
          🤖 {locale === 'bm' ? 'AI Cadangan' : 'AI recommendation'}
        </div>
        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded" style={{ color: confidenceColor, border: `1px solid ${confidenceColor}60` }}>
          {rec.confidence || 'medium'}
        </span>
      </div>
      <div className="text-[12px] leading-relaxed mb-1.5 text-white">{reasoning}</div>
      {rec.suggested_drone && (
        <div className="text-[10px] font-mono" style={{ color: '#9EB0C8' }}>
          {locale === 'bm' ? 'Drone dicadang' : 'Suggested drone'}: <span style={{ color: '#FFCC00' }}>{rec.suggested_drone}</span>
        </div>
      )}
    </div>
  )
}

export default function CoachConsole() {
  const coachLog = useMissionStore(s => s.coachLog)
  const recommendation = useMissionStore(s => s.recommendation)
  const currentCard = useMissionStore(s => s.currentCard)
  const narratorLog = useMissionStore(s => s.narratorLog)
  const locale = useMissionStore(s => s.locale)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [coachLog, narratorLog])

  return (
    <div className="h-full flex flex-col" style={{ background: '#0F1C33' }}>
      <div className="px-3 py-2 text-[10px] uppercase tracking-widest border-b flex items-center justify-between"
        style={{ color: '#FFCC00', borderColor: '#1E3A5F' }}>
        <span>🧠 {locale === 'bm' ? 'Pemikiran AI langsung' : 'Live AI reasoning'}</span>
        <span className="text-[9px] font-mono" style={{ color: '#7A8BA3' }}>
          {coachLog.length} events
        </span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-1">
        {/* Also show narrator intro lines to not lose the opening briefing */}
        {narratorLog.filter(e => e.tone === 'intro').map(entry => (
          <div key={entry.id} className="mb-2">
            <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: '#00D4FF' }}>
              {entry.speaker}
            </div>
            <div className="text-[12px] leading-relaxed" style={{ color: '#E6F0FA' }}>
              {(locale === 'bm' ? entry.text_bm : entry.text_en) || entry.text_en}
            </div>
          </div>
        ))}
        {coachLog.length === 0 && (
          <div className="text-xs italic" style={{ color: '#7A8BA3' }}>
            {locale === 'bm'
              ? 'Menunggu panggilan pertama — AI akan mula berfikir apabila kad muncul.'
              : 'Waiting for first call — the AI will start thinking when a card appears.'}
          </div>
        )}
        {coachLog.map(entry => <LogEntry key={entry.id} entry={entry} locale={locale} />)}
      </div>
      <RecommendationCard rec={recommendation} locale={locale} currentCard={currentCard} />
    </div>
  )
}
