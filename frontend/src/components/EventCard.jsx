import { useState } from 'react'
import useMissionStore from '../stores/missionStore'
import { chooseOption } from '../hooks/useGameApi'

export default function EventCard() {
  const card = useMissionStore(s => s.currentCard)
  const locale = useMissionStore(s => s.locale)
  const [busy, setBusy] = useState(false)

  if (!card) return null

  const lang = locale === 'bm' ? 'bm' : 'en'
  const title = card[`title_${lang}`] || card.title_en
  const body = card[`body_${lang}`] || card.body_en

  const onChoose = async (optionId) => {
    if (busy) return
    setBusy(true)
    try {
      await chooseOption(card.id, optionId)
    } catch (e) {
      console.error('[choose] failed', e)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="absolute z-30 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(480px,92vw)] rounded-xl shadow-2xl"
      style={{
        background: 'linear-gradient(180deg, #1A2847 0%, #0F1C33 100%)',
        border: '1px solid #00D4FF80',
        boxShadow: '0 0 80px #00D4FF30, 0 20px 60px rgba(0,0,0,0.7)',
      }}
    >
      <div className="p-5 border-b" style={{ borderColor: '#1E3A5F' }}>
        <div className="text-[10px] uppercase tracking-widest mb-1" style={{ color: '#00D4FF' }}>
          📞 {locale === 'bm' ? 'Panggilan masuk' : 'Incoming call'} — ({card.coord?.[0]}, {card.coord?.[1]})
        </div>
        <div className="text-lg font-semibold text-white">{title}</div>
        <div className="mt-2 text-sm leading-relaxed" style={{ color: '#C4D4E6' }}>{body}</div>
      </div>
      <div className="p-3 flex flex-col gap-2">
        {card.options.map(opt => (
          <button
            key={opt.id}
            disabled={busy}
            onClick={() => onChoose(opt.id)}
            className="text-left px-4 py-3 rounded-md transition-all disabled:opacity-50"
            style={{
              background: '#1E3A5F',
              border: '1px solid #2E5480',
              color: '#E6F0FA',
            }}
            onMouseEnter={e => {
              if (!busy) {
                e.currentTarget.style.background = '#2E5480'
                e.currentTarget.style.borderColor = '#00D4FF'
              }
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = '#1E3A5F'
              e.currentTarget.style.borderColor = '#2E5480'
            }}
          >
            <div className="text-sm">{opt[`label_${lang}`] || opt.label_en}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
