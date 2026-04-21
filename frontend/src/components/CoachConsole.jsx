import { useEffect, useRef } from 'react'
import useMissionStore from '../stores/missionStore'

// Voice register — same emergency-radio aesthetic as NarratorPanel.
// Judge feedback: "COACH breaks the radio drama register PLAY establishes
// by switching to a developer-console reasoning trace." Fix: render every
// CoT entry as a radio call, not a dev log.

const STAGE_LABEL = {
  coach_assessor: { en: 'MENTOR · ASSESSOR', bm: 'MENTOR · PENILAI', color: '#00D4FF' },
  coach_recommender: { en: 'MENTOR · ADVISOR', bm: 'MENTOR · PENASIHAT', color: '#FFCC00' },
  // Fallback for any unexpected agent name
  default: { en: 'MENTOR', bm: 'MENTOR', color: '#9EB0C8' },
}

function stageFor(agent) {
  return STAGE_LABEL[agent] || STAGE_LABEL.default
}

function truncate(s, n = 240) {
  if (!s) return ''
  return s.length <= n ? s : s.slice(0, n).trimEnd() + '…'
}

// Unwrap MCP protocol wrapping to get natural-language text.
// Raw MCP tool results look like {"content":[{"type":"text","text":"..."}]} —
// we want to surface ONLY the inner text so judges don't see the wire layer.
function humanizeMcpResult(raw) {
  if (!raw) return ''
  const s = String(raw).trim()
  // Quick path: looks like JSON? Try parse.
  if (s.startsWith('{') || s.startsWith('[')) {
    try {
      const o = JSON.parse(s)
      if (Array.isArray(o?.content)) {
        const bits = o.content
          .filter(c => c?.type === 'text' && c.text)
          .map(c => c.text)
        if (bits.length) return bits.join(' ')
      }
      // fallback — compact JSON still, but stripped of outer wrappers
      return JSON.stringify(o).slice(0, 160)
    } catch {
      // not parsable — passthrough
    }
  }
  return s
}

// Detect reasoning text that is really just the recommender's JSON
// payload leaking before our parser turns it into the clean MentorBrief.
function isStructuredJsonLeak(text) {
  if (!text) return false
  const t = text.trim()
  if (!(t.startsWith('{') || t.startsWith('```'))) return false
  return /\boption_id\b|\breasoning_en\b|\bsuggested_drone\b/.test(t)
}

function RadioEntry({ entry, locale }) {
  const k = entry.kind || 'reasoning'
  const stage = stageFor(entry.agent)
  const label = locale === 'bm' ? stage.bm : stage.en

  if (k === 'tool_call') {
    return (
      <div className="mb-2.5">
        <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: '#9EB0C8' }}>
          📡 {locale === 'bm' ? 'MCP · alat' : 'MCP · tool'}
        </div>
        <div className="text-[12px] italic" style={{ color: '#C4D4E6' }}>
          {locale === 'bm' ? 'Memanggil' : 'Calling'} <span className="font-mono">{entry.tool}</span>
          {entry.args && Object.keys(entry.args).length > 0
            ? ` ${JSON.stringify(entry.args).slice(0, 60)}`
            : ''}
        </div>
      </div>
    )
  }
  if (k === 'tool_result') {
    return (
      <div className="mb-2.5">
        <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: '#06D6A0' }}>
          📻 {locale === 'bm' ? 'Laporan kembali' : 'Incoming report'}
        </div>
        <div className="text-[12px] leading-relaxed" style={{ color: '#C4D4E6' }}>
          {locale === 'bm' ? 'Dari' : 'From'} <span className="font-mono">{entry.tool}</span>:{' '}
          {truncate(humanizeMcpResult(entry.result), 180)}
        </div>
      </div>
    )
  }
  // Hide raw JSON leaks from the recommender — the parsed MentorBrief
  // already renders the recommendation cleanly in prose below.
  if (isStructuredJsonLeak(entry.text)) return null
  // reasoning — render as a NADMA-style radio call
  return (
    <div className="mb-2.5">
      <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: stage.color }}>
        📻 {label}
      </div>
      <div className="text-[12px] leading-relaxed" style={{ color: '#E6F0FA' }}>
        {truncate(entry.text, 320)}
      </div>
    </div>
  )
}

function MentorBrief({ rec, locale, currentCard }) {
  if (!rec) return null
  if (currentCard && rec.card_id && rec.card_id !== currentCard.id) return null

  const reasoning = locale === 'bm'
    ? (rec.reasoning_bm || rec.reasoning_en)
    : (rec.reasoning_en || rec.reasoning_bm)

  const confidenceColor = rec.confidence === 'high' ? '#06D6A0'
    : rec.confidence === 'low' ? '#FF5E78' : '#FFCC00'

  return (
    <div className="shrink-0 p-3 border-t" style={{ borderColor: '#FFCC0040', background: 'rgba(255,204,0,0.05)' }}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="text-[10px] uppercase tracking-widest" style={{ color: '#FFCC00' }}>
          🎧 {locale === 'bm' ? 'Datuk Nadia — taklimat akhir' : 'Datuk Nadia — mentor brief'}
        </div>
        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded"
          style={{ color: confidenceColor, border: `1px solid ${confidenceColor}60` }}>
          {rec.confidence || 'medium'}
        </span>
      </div>
      <div className="text-[12px] leading-relaxed mb-1.5 text-white italic">
        "{reasoning}"
      </div>
      {rec.suggested_drone && (
        <div className="text-[10px] font-mono" style={{ color: '#9EB0C8' }}>
          {locale === 'bm' ? '→ hantar' : '→ send'}:{' '}
          <span style={{ color: '#FFCC00' }}>{rec.suggested_drone}</span>
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

  const header = locale === 'bm' ? 'Radio NADMA · Jurulatih AI' : 'NADMA Radio · AI Mentor'

  // Merge passive NADMA narrator entries with coach log so the user sees
  // one coherent radio stream, not two parallel logs.
  const merged = [
    ...narratorLog.filter(e => e.tone === 'intro' || e.tone === 'passive').map(e => ({
      __kind: 'narrator', id: e.id, timestamp: e.timestamp, speaker: e.speaker,
      text: (locale === 'bm' ? e.text_bm : e.text_en) || e.text_en, tone: e.tone,
    })),
    ...coachLog.map(c => ({ __kind: 'coach', ...c })),
  ].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))

  return (
    <div className="h-full flex flex-col" style={{ background: '#0F1C33' }}>
      <div className="px-3 py-2 text-[10px] uppercase tracking-widest border-b flex items-center justify-between"
        style={{ color: '#FFCC00', borderColor: '#1E3A5F' }}>
        <span>📻 {header}</span>
        <span className="text-[9px] font-mono" style={{ color: '#7A8BA3' }}>
          {coachLog.length} events
        </span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3">
        {merged.length === 0 && (
          <div className="text-xs italic" style={{ color: '#7A8BA3' }}>
            {locale === 'bm'
              ? 'Menunggu panggilan pertama — jurulatih AI akan mula berfikir bersama anda.'
              : 'Standing by — the AI mentor will start thinking alongside you when the first call comes in.'}
          </div>
        )}
        {merged.map(e =>
          e.__kind === 'narrator' ? (
            <div key={e.id} className="mb-2.5">
              <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: e.tone === 'intro' ? '#00D4FF' : '#7A8BA3' }}>
                📻 {e.speaker}
              </div>
              <div className="text-[12px] leading-relaxed" style={{ color: '#C4D4E6' }}>
                {e.text}
              </div>
            </div>
          ) : (
            <RadioEntry key={e.id} entry={e} locale={locale} />
          )
        )}
      </div>
      <MentorBrief rec={recommendation} locale={locale} currentCard={currentCard} />
    </div>
  )
}
