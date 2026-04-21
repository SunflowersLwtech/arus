import { useEffect, useRef } from 'react'
import useMissionStore from '../stores/missionStore'

export default function NarratorPanel() {
  const log = useMissionStore(s => s.narratorLog)
  const locale = useMissionStore(s => s.locale)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [log])

  return (
    <div className="h-full flex flex-col" style={{ background: '#0F1C33' }}>
      <div className="px-4 py-2 text-[10px] uppercase tracking-widest border-b" style={{ color: '#00D4FF', borderColor: '#1E3A5F' }}>
        📻 {locale === 'bm' ? 'Radio NADMA' : 'NADMA Radio'}
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3 text-sm">
        {log.length === 0 && (
          <div className="text-xs italic" style={{ color: '#7A8BA3' }}>
            {locale === 'bm' ? 'Menunggu komunikasi...' : 'Standing by…'}
          </div>
        )}
        {log.map(entry => {
          const text = (locale === 'bm' ? entry.text_bm : entry.text_en) || entry.text_en || entry.text_bm
          return (
            <div key={entry.id}>
              <div className="text-[10px] uppercase tracking-wider mb-0.5" style={{ color: entry.tone === 'intro' ? '#00D4FF' : '#9EB0C8' }}>
                {entry.speaker || 'SYS'}
              </div>
              <div className="leading-relaxed" style={{ color: '#E6F0FA' }}>{text}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
