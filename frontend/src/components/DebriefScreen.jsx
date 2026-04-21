import { useEffect, useState } from 'react'
import useMissionStore from '../stores/missionStore'
import { fetchDebrief, startGame } from '../hooks/useGameApi'

export default function DebriefScreen() {
  const gameStatus = useMissionStore(s => s.gameStatus)
  const debrief = useMissionStore(s => s.debrief)
  const resetGame = useMissionStore(s => s.resetGame)
  const locale = useMissionStore(s => s.locale)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if ((gameStatus === 'won' || gameStatus === 'partial' || gameStatus === 'failed') && !debrief && !loaded) {
      setLoaded(true)
      fetchDebrief().catch(e => console.error('debrief fetch failed', e))
    }
  }, [gameStatus, debrief, loaded])

  if (!debrief) return null

  const lang = locale === 'bm' ? 'bm' : 'en'
  const copy = locale === 'bm' ? {
    heading: 'Ringkasan Misi',
    yours: 'Keputusan anda',
    real: 'Apa yang sebenarnya berlaku',
    next: 'Teruskan pembelajaran',
    again: 'Main semula',
    saved: 'Diselamatkan',
    target: 'Sasaran',
    trust: 'Kepercayaan',
    assets: 'Aset tinggal',
    grade: 'Gred',
    timeline: 'Garis masa keputusan',
    noChoices: 'Tiada keputusan direkodkan.',
    status: {
      won: 'Anda berjaya selaraskan penyelamatan di tengah kekacauan.',
      partial: 'Anda menyelamatkan sebahagian. Banyak yang masih tidak dijawab.',
      failed: 'Penyelarasan runtuh sebelum misi tamat.',
    },
  } : {
    heading: 'Mission Debrief',
    yours: 'Your results',
    real: 'What actually happened',
    next: 'Keep learning',
    again: 'Play again',
    saved: 'Saved',
    target: 'Target',
    trust: 'Trust',
    assets: 'Assets left',
    grade: 'Grade',
    timeline: 'Decision timeline',
    noChoices: 'No decisions logged.',
    status: {
      won: 'You coordinated rescue under pressure. Cleanly done.',
      partial: 'You saved some. Many calls went unanswered.',
      failed: 'Coordination collapsed before the session ended.',
    },
  }

  const real = debrief.real_event || {}
  const lessons = real.key_lessons?.[lang] || real.key_lessons?.en || []

  const onRestart = async () => {
    resetGame()
    try {
      await startGame('shah_alam_hard', locale)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="absolute inset-0 z-50 overflow-y-auto" style={{ background: 'rgba(6,13,27,0.96)' }}>
      <div className="min-h-full flex items-start justify-center p-6">
        <div
          className="w-[min(720px,96vw)] my-8 rounded-xl"
          style={{
            background: 'linear-gradient(180deg, #112346 0%, #0B1426 100%)',
            border: '1px solid #00D4FF40',
          }}
        >
          <div className="p-6 border-b" style={{ borderColor: '#1E3A5F' }}>
            <div className="text-xs uppercase tracking-widest mb-1" style={{ color: '#00D4FF' }}>
              {copy.heading}
            </div>
            <div className="text-2xl font-bold text-white mb-2">{copy.status[debrief.status] || debrief.status}</div>
            <div className="flex items-center gap-4 mt-3">
              <div className="text-5xl font-bold" style={{ color: '#00D4FF' }}>{debrief.grade}</div>
              <div className="text-xs" style={{ color: '#7A8BA3' }}>{copy.grade}</div>
            </div>
          </div>

          {/* Gemini-authored NADMA commentary */}
          {debrief.commentary && (
            <div className="p-6 border-b" style={{ borderColor: '#1E3A5F', background: 'rgba(0,212,255,0.03)' }}>
              <div className="text-xs uppercase tracking-widest mb-3" style={{ color: '#00D4FF' }}>
                📻 {locale === 'bm' ? 'Ulasan NADMA · Datuk Nadia' : 'NADMA commentary · Datuk Nadia'}
                {debrief.commentary.source === 'fallback' && (
                  <span className="ml-2 text-[9px] opacity-60">(offline mode)</span>
                )}
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: '#E6F0FA' }}>
                {(locale === 'bm' ? debrief.commentary.bm : debrief.commentary.en) || debrief.commentary.en}
              </div>
            </div>
          )}

          {/* Your numbers */}
          <div className="p-6 border-b" style={{ borderColor: '#1E3A5F' }}>
            <div className="text-xs uppercase tracking-widest mb-3" style={{ color: '#00D4FF' }}>{copy.yours}</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <Stat label={copy.saved} value={`${debrief.gauges.saved} / ${debrief.target_saved}`} />
              <Stat label={copy.trust} value={`${Math.round(debrief.gauges.trust)}%`} />
              <Stat label={copy.assets} value={`${Math.round(debrief.gauges.assets)}%`} />
              <Stat label={copy.target} value={debrief.target_saved} />
            </div>
          </div>

          {/* Decision timeline */}
          {debrief.choices && debrief.choices.length > 0 && (
            <div className="p-6 border-b" style={{ borderColor: '#1E3A5F' }}>
              <div className="text-xs uppercase tracking-widest mb-3" style={{ color: '#00D4FF' }}>{copy.timeline}</div>
              <div className="space-y-2">
                {debrief.choices.map((c, i) => (
                  <TimelineRow key={i} index={i + 1} choice={c} locale={locale} />
                ))}
              </div>
            </div>
          )}

          {/* Real comparison */}
          <div className="p-6 border-b" style={{ borderColor: '#1E3A5F' }}>
            <div className="text-xs uppercase tracking-widest mb-2" style={{ color: '#00D4FF' }}>{copy.real}</div>
            <div className="text-sm font-semibold text-white mb-2">{real[`name_${lang}`] || real.name_en}</div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs mb-4" style={{ color: '#9EB0C8' }}>
              {real.displaced != null && <Stat label={locale === 'bm' ? 'Dipindahkan' : 'Displaced'} value={real.displaced.toLocaleString()} />}
              {real.deaths != null && <Stat label={locale === 'bm' ? 'Meninggal' : 'Deaths'} value={real.deaths} />}
              {real.response_time_hours_median != null && <Stat label={locale === 'bm' ? 'Waktu respons (jam)' : 'Response time (h)'} value={real.response_time_hours_median} />}
              {real.agencies_involved != null && <Stat label={locale === 'bm' ? 'Agensi' : 'Agencies'} value={real.agencies_involved} />}
            </div>
            <ul className="list-disc pl-5 text-sm space-y-1" style={{ color: '#C4D4E6' }}>
              {lessons.map((l, i) => <li key={i}>{l}</li>)}
            </ul>
            {real.sources && real.sources.length > 0 && (
              <div className="mt-3 text-[11px]" style={{ color: '#7A8BA3' }}>
                {locale === 'bm' ? 'Sumber:' : 'Sources:'}{' '}
                {real.sources.map((s, i) => (
                  <a key={i} href={s} target="_blank" rel="noreferrer" className="underline mr-2" style={{ color: '#00D4FF' }}>
                    [{i + 1}]
                  </a>
                ))}
              </div>
            )}
          </div>

          {/* Extension links */}
          <div className="p-6 border-b" style={{ borderColor: '#1E3A5F' }}>
            <div className="text-xs uppercase tracking-widest mb-3" style={{ color: '#00D4FF' }}>{copy.next}</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
              {Object.entries(debrief.extension_links || {}).map(([k, url]) => (
                <a
                  key={k}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-2 rounded text-center"
                  style={{ background: '#1E3A5F', color: '#E6F0FA', border: '1px solid #2E5480' }}
                >
                  {linkLabel(k, locale)}
                </a>
              ))}
            </div>
          </div>

          <div className="p-6">
            <button
              onClick={onRestart}
              className="w-full px-6 py-3 rounded-md font-semibold"
              style={{ background: '#00D4FF', color: '#0B1426' }}
            >
              {copy.again}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider" style={{ color: '#7A8BA3' }}>{label}</div>
      <div className="text-base font-semibold text-white">{value}</div>
    </div>
  )
}

const AGENCY_COLORS_DBG = {
  BOMBA: '#FF6A3D', APM: '#06D6A0', MMEA: '#4DA8DA', NADMA: '#FFCC00',
}

function DeltaPill({ value, suffix = '', good }) {
  if (value == null || value === 0) return null
  const positive = value > 0
  const aligns = good === undefined ? positive : (positive === good)
  const color = aligns ? '#06D6A0' : '#FF5E78'
  return (
    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded"
      style={{ color, background: `${color}15`, border: `1px solid ${color}30` }}>
      {positive ? '+' : ''}{value}{suffix}
    </span>
  )
}

function TimelineRow({ index, choice, locale }) {
  const title = (locale === 'bm' ? choice.card_title_bm : choice.card_title_en) || choice.card_id
  const label = (locale === 'bm' ? choice.option_label_bm : choice.option_label_en) || choice.option_id
  const flavor = (locale === 'bm' ? choice.flavor?.bm : choice.flavor?.en) || choice.flavor?.en || ''
  const agencyColor = choice.agency ? AGENCY_COLORS_DBG[choice.agency] : '#00D4FF'
  return (
    <div className="rounded p-3 text-sm" style={{ background: '#0F1C33', border: '1px solid #1E3A5F' }}>
      <div className="flex items-center gap-2 mb-1">
        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-mono font-bold"
          style={{ background: agencyColor, color: '#0B1426' }}>
          {index}
        </span>
        <span className="font-semibold text-white flex-1">{title}</span>
        {choice.agency && (
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded"
            style={{ color: agencyColor, background: `${agencyColor}20`, border: `1px solid ${agencyColor}50` }}>
            ✈ {choice.agency}
          </span>
        )}
      </div>
      <div className="text-[12px] mb-1.5" style={{ color: '#9EB0C8' }}>→ {label}</div>
      {flavor && (
        <div className="text-[11px] italic mb-1.5" style={{ color: '#C4D4E6' }}>{flavor}</div>
      )}
      {choice.deltas && (
        <div className="flex flex-wrap gap-1">
          <DeltaPill value={choice.deltas.saved} good={true} />
          <DeltaPill value={choice.deltas.assets} suffix="%" good={false} />
          <DeltaPill value={choice.deltas.trust} suffix="%" good={true} />
        </div>
      )}
    </div>
  )
}

function linkLabel(key, locale) {
  const L = {
    nadma_portal_bencana: { en: 'NADMA · Portal Bencana', bm: 'NADMA · Portal Bencana' },
    public_infobanjir: { en: 'Public InfoBanjir (water levels)', bm: 'Public InfoBanjir (paras air)' },
    metmalaysia_warnings: { en: 'MetMalaysia warnings API', bm: 'API amaran MetMalaysia' },
  }
  return L[key]?.[locale] || L[key]?.en || key.replace(/_/g, ' ')
}
