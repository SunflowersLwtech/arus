import { useEffect, useRef, useState } from 'react'
import useMissionStore from '../stores/missionStore'
import { chooseOption } from '../hooks/useGameApi'

const CARD_PRESSURE_SECONDS = 45

function DeltaChip({ value, suffix, good, label }) {
  if (value == null || value === 0) return null
  const positive = value > 0
  const aligns = good === undefined ? positive : (positive === good)
  const color = aligns ? '#06D6A0' : '#FF5E78'
  const sign = positive ? '+' : ''
  return (
    <span
      className="inline-flex items-center gap-0.5 text-[10px] font-mono px-1.5 py-0.5 rounded"
      style={{ color, background: `${color}15`, border: `1px solid ${color}30` }}
      title={label}
    >
      {sign}{value}{suffix}
      <span className="opacity-60 ml-0.5">{label}</span>
    </span>
  )
}

const AGENCY_COLORS = {
  BOMBA: '#FF6A3D',
  APM:   '#06D6A0',
  MMEA:  '#4DA8DA',
  NADMA: '#FFCC00',
}

function AgencyBadge({ agency, locale }) {
  if (!agency) return null
  const c = AGENCY_COLORS[agency] || '#00D4FF'
  const label = locale === 'bm' ? `Drone: ${agency}` : `Dispatches: ${agency}`
  return (
    <span
      className="inline-flex items-center gap-0.5 text-[10px] font-mono px-1.5 py-0.5 rounded"
      style={{ color: c, background: `${c}15`, border: `1px solid ${c}40` }}
    >
      ✈ {label}
    </span>
  )
}

function OptionDeltas({ deltas, agency, locale, agencyBusy }) {
  if (!deltas) return null
  const labels = locale === 'bm'
    ? { saved: 'nyawa', assets: 'aset', trust: 'kepercayaan' }
    : { saved: 'lives', assets: 'assets', trust: 'trust' }
  return (
    <div className="flex flex-wrap gap-1 mt-1.5">
      <DeltaChip value={deltas.saved} suffix="" good={true} label={labels.saved} />
      <DeltaChip value={deltas.assets} suffix="%" good={false} label={labels.assets} />
      <DeltaChip value={deltas.trust} suffix="%" good={true} label={labels.trust} />
      <AgencyBadge agency={agency} locale={locale} />
      {agencyBusy && (
        <span
          className="inline-flex items-center gap-0.5 text-[10px] font-mono px-1.5 py-0.5 rounded"
          style={{ color: '#FF5E78', background: '#FF5E7815', border: '1px solid #FF5E7860' }}
          title="No idle drone for this agency — response will be degraded (~half lives saved)."
        >
          ⚠ {locale === 'bm' ? 'aset sibuk' : 'busy'}
        </span>
      )}
    </div>
  )
}

export default function EventCard() {
  const card = useMissionStore(s => s.currentCard)
  const locale = useMissionStore(s => s.locale)
  const mode = useMissionStore(s => s.mode)
  const recommendation = useMissionStore(s => s.recommendation)
  const fleet = useMissionStore(s => s.fleet)
  const [busy, setBusy] = useState(false)
  const [pressureRemaining, setPressureRemaining] = useState(CARD_PRESSURE_SECONDS)
  const startTimeRef = useRef(null)
  const cardIdRef = useRef(null)

  // Date.now-based countdown — immune to React re-renders and setInterval drift
  // (the previous setInterval-accumulator approach plateaued near the end).
  useEffect(() => {
    if (!card) return
    if (cardIdRef.current !== card.id) {
      cardIdRef.current = card.id
      startTimeRef.current = Date.now()
      setPressureRemaining(CARD_PRESSURE_SECONDS)
    }
    const compute = () => {
      const elapsed = (Date.now() - (startTimeRef.current || Date.now())) / 1000
      setPressureRemaining(Math.max(0, CARD_PRESSURE_SECONDS - elapsed))
    }
    compute()
    const handle = setInterval(compute, 150)
    return () => clearInterval(handle)
  }, [card?.id])

  if (!card) return null

  const pressurePct = Math.max(0, Math.min(100, (pressureRemaining / CARD_PRESSURE_SECONDS) * 100))
  const pressureColor = pressureRemaining < 10 ? '#FF4F5E' : pressureRemaining < 20 ? '#FFB84D' : '#00D4FF'
  const displaySeconds = pressureRemaining >= 1
    ? Math.floor(pressureRemaining)
    : pressureRemaining.toFixed(1)

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
      className="absolute z-30 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(520px,94vw)] rounded-xl shadow-2xl overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, #1A2847 0%, #0F1C33 100%)',
        border: '1px solid #00D4FF80',
        boxShadow: '0 0 80px #00D4FF30, 0 20px 60px rgba(0,0,0,0.7)',
      }}
    >
      {/* Pressure bar — shrinks over 45 seconds to add felt urgency (no mechanical penalty). */}
      <div className="h-1" style={{ background: '#0B1426' }}>
        <div
          className="h-full transition-all duration-200 ease-linear"
          style={{ width: `${pressurePct}%`, background: pressureColor }}
        />
      </div>

      <div className="p-5 border-b" style={{ borderColor: '#1E3A5F' }}>
        <div className="flex items-center justify-between mb-1">
          <div className="text-[10px] uppercase tracking-widest" style={{ color: '#00D4FF' }}>
            📞 {locale === 'bm' ? 'Panggilan masuk' : 'Incoming call'} — ({card.coord?.[0]}, {card.coord?.[1]})
          </div>
          <div className="text-[10px] font-mono" style={{ color: pressureColor }}>
            {displaySeconds}s
          </div>
        </div>
        <div className="text-lg font-semibold text-white">{title}</div>
        <div className="mt-2 text-sm leading-relaxed" style={{ color: '#C4D4E6' }}>{body}</div>
      </div>
      <div className="p-3 flex flex-col gap-2">
        {card.options.map(opt => {
          const isRecommended = (
            mode === 'COACH'
            && recommendation
            && recommendation.card_id === card.id
            && recommendation.option_id === opt.id
          )
          const baseBg = isRecommended ? 'rgba(255,204,0,0.12)' : '#1E3A5F'
          const baseBorder = isRecommended ? '#FFCC00' : '#2E5480'
          return (
            <button
              key={opt.id}
              disabled={busy}
              onClick={() => onChoose(opt.id)}
              className="text-left px-4 py-3 rounded-md transition-all disabled:opacity-50 relative"
              style={{ background: baseBg, border: `1px solid ${baseBorder}`, color: '#E6F0FA' }}
              onMouseEnter={e => {
                if (!busy) {
                  e.currentTarget.style.background = isRecommended ? 'rgba(255,204,0,0.18)' : '#2E5480'
                  e.currentTarget.style.borderColor = isRecommended ? '#FFCC00' : '#00D4FF'
                }
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = baseBg
                e.currentTarget.style.borderColor = baseBorder
              }}
            >
              {isRecommended && (
                <span className="absolute -top-2 left-3 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded"
                  style={{ background: '#FFCC00', color: '#0B1426' }}>
                  🤖 {locale === 'bm' ? 'AI cadang' : 'AI suggests'}
                </span>
              )}
              <div className="text-sm">{opt[`label_${lang}`] || opt.label_en}</div>
              <OptionDeltas
                deltas={opt.deltas}
                agency={opt.agency}
                locale={locale}
                agencyBusy={Boolean(opt.agency) && !fleet.some(u => u.agency === opt.agency && u.status === 'idle')}
              />
            </button>
          )
        })}
      </div>
    </div>
  )
}
