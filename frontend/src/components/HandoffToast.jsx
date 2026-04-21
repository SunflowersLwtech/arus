import { useEffect, useState } from 'react'
import useMissionStore from '../stores/missionStore'

const AGENCY_COLORS = {
  BOMBA: '#FF6A3D',
  APM: '#06D6A0',
  MMEA: '#4DA8DA',
  NADMA: '#FFCC00',
}

// AUTO mode's stage-5 agency dispatcher emits structured BM/EN briefs.
// We surface each one as a ~8-second toast so judges see "this is the
// WhatsApp BOMBA would actually receive", not just a log entry.
export default function HandoffToast() {
  const latest = useMissionStore(s => s.latestHandoff)
  const locale = useMissionStore(s => s.locale)
  const [visible, setVisible] = useState(false)
  const [renderedTs, setRenderedTs] = useState(null)

  useEffect(() => {
    if (!latest || latest.ts === renderedTs) return
    setRenderedTs(latest.ts)
    setVisible(true)
    const t = setTimeout(() => setVisible(false), 8000)
    return () => clearTimeout(t)
  }, [latest, renderedTs])

  if (!latest || !visible) return null

  const color = AGENCY_COLORS[latest.agency] || '#FFCC00'
  const label = locale === 'bm' ? 'WhatsApp agensi (automatik)' : 'Agency WhatsApp (auto-drafted)'

  return (
    <div
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 w-[min(460px,92vw)] rounded-lg shadow-2xl animate-fadeIn"
      style={{
        background: '#0F1C33',
        border: `1px solid ${color}`,
        boxShadow: `0 0 40px ${color}40`,
      }}
    >
      <div className="px-4 py-2 flex items-center justify-between border-b"
        style={{ borderColor: `${color}40` }}>
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full animate-pulse" style={{ background: color }} />
          <span className="text-[10px] uppercase tracking-widest" style={{ color }}>
            📱 {label} · {latest.agency}
          </span>
        </div>
        <span className="text-[10px] font-mono" style={{ color: '#7A8BA3' }}>
          {latest.coord || ''} · {(latest.priority || '').toUpperCase()}
        </span>
      </div>
      <div className="p-3 text-[12px] leading-relaxed space-y-1.5" style={{ color: '#E6F0FA' }}>
        {latest.bm && <div><span className="text-[9px] font-mono" style={{ color: '#7A8BA3' }}>BM</span> {latest.bm}</div>}
        {latest.en && <div><span className="text-[9px] font-mono" style={{ color: '#7A8BA3' }}>EN</span> {latest.en}</div>}
        {latest.action && (
          <div className="mt-1 pt-1.5 border-t text-[11px] italic" style={{ borderColor: '#1E3A5F', color: '#9EB0C8' }}>
            → {latest.action}
          </div>
        )}
      </div>
    </div>
  )
}
