import { useState } from 'react'
import useMissionStore from '../stores/missionStore'
import { startGame } from '../hooks/useGameApi'

export default function StartScreen() {
  const locale = useMissionStore(s => s.locale)
  const setLocale = useMissionStore(s => s.setLocale)
  const [busy, setBusy] = useState(false)

  const copy = locale === 'bm'
    ? {
        title: 'Banjir Drill',
        subtitle: 'Simulasi penyelarasan bencana untuk rakyat Malaysia',
        body: 'Anda ialah pegawai penyelaras NADMA malam Banjir Besar 2021. Empat agensi. Aset terhad. 7 minit bermain.',
        howto_heading: 'Cara bermain',
        howto: [
          'Baca panggilan masuk. Pilih satu daripada 2–3 tindakan.',
          'Setiap tindakan menggerakkan drone agensi yang betul di peta.',
          'Semasa menunggu, klik drone di bar kiri → klik peta untuk hantar manual.',
          'Tamat dalam 7 minit: kad taklimat + ulasan NADMA + data sebenar 2021.',
        ],
        cta: 'Mula bermain',
        cta_hint: 'Perlahan — ulasan menunggu di akhir.',
      }
    : {
        title: 'Banjir Drill',
        subtitle: 'A disaster-coordination simulator for Malaysian citizens',
        body: 'You are NADMA\'s coordinating officer on the night of the 2021 Klang Valley floods. Four agencies. Limited assets. 7 minutes.',
        howto_heading: 'How to play',
        howto: [
          'Read each incoming call. Pick one of 2–3 response options.',
          'Your choice moves the matching agency\'s drone on the map.',
          'Between calls: tap a drone in the left sidebar → tap the map to send it anywhere.',
          'At the end: grade + NADMA commentary + real 2021 Shah Alam data.',
        ],
        cta: 'Start drill',
        cta_hint: 'Take your time — a full debrief waits at the end.',
      }

  const onStart = async () => {
    if (busy) return
    setBusy(true)
    try {
      await startGame('shah_alam_hard', locale)
    } catch (e) {
      console.error(e)
      setBusy(false)
    }
  }

  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center" style={{ background: 'rgba(6,13,27,0.85)' }}>
      <div
        className="w-[min(560px,92vw)] rounded-xl p-8"
        style={{
          background: 'linear-gradient(180deg, #112346 0%, #0B1426 100%)',
          border: '1px solid #00D4FF60',
          boxShadow: '0 0 100px #00D4FF20',
        }}
      >
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="text-xs uppercase tracking-widest mb-1" style={{ color: '#00D4FF' }}>Arus · Track 2</div>
            <div className="text-3xl font-bold text-white">{copy.title}</div>
          </div>
          <div className="flex gap-1 text-xs">
            <button
              onClick={() => setLocale('bm')}
              className="px-2 py-1 rounded"
              style={{
                background: locale === 'bm' ? '#00D4FF' : '#1E3A5F',
                color: locale === 'bm' ? '#0B1426' : '#C4D4E6',
              }}
            >BM</button>
            <button
              onClick={() => setLocale('en')}
              className="px-2 py-1 rounded"
              style={{
                background: locale === 'en' ? '#00D4FF' : '#1E3A5F',
                color: locale === 'en' ? '#0B1426' : '#C4D4E6',
              }}
            >EN</button>
          </div>
        </div>

        <div className="text-sm mb-2" style={{ color: '#9EB0C8' }}>{copy.subtitle}</div>
        <div className="text-base leading-relaxed mb-5 text-white">{copy.body}</div>

        <div className="mb-6 p-3 rounded" style={{ background: '#0B1426', border: '1px solid #1E3A5F' }}>
          <div className="text-[10px] uppercase tracking-widest mb-2" style={{ color: '#00D4FF' }}>
            {copy.howto_heading}
          </div>
          <ol className="text-[13px] leading-relaxed space-y-1 pl-4 list-decimal" style={{ color: '#C4D4E6' }}>
            {copy.howto.map((line, i) => <li key={i}>{line}</li>)}
          </ol>
        </div>

        <button
          onClick={onStart}
          disabled={busy}
          className="w-full px-6 py-3 rounded-md font-semibold transition-all disabled:opacity-50"
          style={{ background: '#00D4FF', color: '#0B1426' }}
        >
          {busy ? '…' : copy.cta}
        </button>
        <div className="mt-2 text-xs text-center" style={{ color: '#7A8BA3' }}>{copy.cta_hint}</div>
      </div>
    </div>
  )
}
