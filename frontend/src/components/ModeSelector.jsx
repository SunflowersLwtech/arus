import useMissionStore from '../stores/missionStore'

const MODES = [
  {
    id: 'PLAY',
    label_en: 'Play',
    label_bm: 'Main',
    hint_en: 'You decide. 8 incoming calls, 7 minutes, no hints.',
    hint_bm: 'Anda yang tentukan. 8 panggilan masuk, 7 minit, tiada petunjuk.',
    color: '#00D4FF',
  },
  {
    id: 'COACH',
    label_en: 'Coach',
    label_bm: 'Jurulatih',
    hint_en: 'An AI mentor streams its reasoning and suggests a drone.',
    hint_bm: 'AI mentor menstrim pemikirannya dan mencadangkan drone.',
    color: '#FFCC00',
  },
  {
    id: 'AUTO',
    label_en: 'Watch AI',
    label_bm: 'Lihat AI',
    hint_en: 'The v1 5-stage ADK pipeline dispatches autonomously via MCP.',
    hint_bm: 'Aliran 5-peringkat ADK mengendalikan secara autonomi melalui MCP.',
    color: '#FF6A3D',
  },
]

export default function ModeSelector({ value, onChange, locale }) {
  return (
    <div className="grid grid-cols-3 gap-2 mb-4">
      {MODES.map(m => {
        const active = m.id === value
        return (
          <button
            key={m.id}
            onClick={() => onChange(m.id)}
            className="rounded-md px-2 py-2 text-left transition-all"
            style={{
              background: active ? `${m.color}25` : '#0B1426',
              border: `1.5px solid ${active ? m.color : '#1E3A5F'}`,
            }}
          >
            <div className="text-[11px] font-semibold" style={{ color: active ? m.color : '#C4D4E6' }}>
              {locale === 'bm' ? m.label_bm : m.label_en}
            </div>
            <div className="text-[10px] mt-0.5 leading-tight" style={{ color: '#7A8BA3' }}>
              {locale === 'bm' ? m.hint_bm : m.hint_en}
            </div>
          </button>
        )
      })}
    </div>
  )
}
