import useMissionStore from '../stores/missionStore'

// Four agencies we track. Keep the labels+colours in lockstep with
// backend/game/agencies.py so the sidebar and the 3D glyphs agree.
const AGENCY_DEFS = [
  { code: 'BOMBA', color: '#FF6A3D', name_en: 'BOMBA · Swift water', name_bm: 'BOMBA · Air deras' },
  { code: 'APM',   color: '#06D6A0', name_en: 'APM · Civil defence', name_bm: 'APM · Pertahanan awam' },
  { code: 'MMEA',  color: '#4DA8DA', name_en: 'MMEA · Maritime',     name_bm: 'MMEA · Maritim' },
  { code: 'NADMA', color: '#FFCC00', name_en: 'NADMA · Coordinator', name_bm: 'NADMA · Penyelaras' },
]

function DroneRow({ uav, selected, onSelect, locale }) {
  const statusLabel = locale === 'bm'
    ? { idle: 'sedia', moving: 'bergerak', scanning: 'mengimbas', returning: 'pulang', charging: 'cas', offline: 'tiada' }
    : { idle: 'idle', moving: 'moving', scanning: 'scanning', returning: 'return', charging: 'charge', offline: 'offline' }

  const s = statusLabel[uav.status] || uav.status

  return (
    <button
      onClick={() => onSelect(uav.id)}
      className="w-full text-left px-2 py-1.5 rounded transition-colors"
      style={{
        background: selected ? `${uav.agency_color}30` : '#111B2E',
        border: `1px solid ${selected ? uav.agency_color : '#1E3A5F'}`,
      }}
      title={`Click to send ${uav.id} to a specific cell — map will enter targeting mode`}
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs font-semibold" style={{ color: uav.agency_color || '#C4D4E6' }}>
          {uav.id}
        </span>
        <span className="text-[10px] font-mono" style={{ color: '#7A8BA3' }}>
          {s} · {Math.round(uav.power || 0)}%
        </span>
      </div>
      <div className="text-[10px] mt-0.5" style={{ color: '#9EB0C8' }}>
        ({uav.x}, {uav.y})
      </div>
    </button>
  )
}

export default function AgencyStatusPanel() {
  const fleet = useMissionStore(s => s.fleet)
  const locale = useMissionStore(s => s.locale)
  const targetingDroneId = useMissionStore(s => s.targetingDroneId)
  const setTargetingDroneId = useMissionStore(s => s.setTargetingDroneId)

  const onSelect = (droneId) => {
    setTargetingDroneId(droneId === targetingDroneId ? null : droneId)
  }

  const header = locale === 'bm' ? 'Aset Agensi' : 'Agency Assets'
  const hint = locale === 'bm'
    ? 'Klik drone, kemudian klik pada peta untuk hantar.'
    : 'Click a drone, then click on the map to dispatch.'

  return (
    <div className="h-full flex flex-col" style={{ background: '#0F1C33' }}>
      <div className="px-3 py-2 border-b" style={{ borderColor: '#1E3A5F' }}>
        <div className="text-[10px] uppercase tracking-widest" style={{ color: '#00D4FF' }}>{header}</div>
        <div className="text-[9px] mt-0.5" style={{ color: '#7A8BA3' }}>{hint}</div>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-3">
        {AGENCY_DEFS.map(a => {
          const drones = fleet.filter(u => u.agency === a.code)
          if (drones.length === 0) return null
          return (
            <div key={a.code}>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="inline-block w-2 h-2 rounded-full" style={{ background: a.color }} />
                <span className="text-[10px] font-mono font-semibold tracking-wider" style={{ color: a.color }}>
                  {locale === 'bm' ? a.name_bm : a.name_en}
                </span>
              </div>
              <div className="space-y-1">
                {drones.map(u => (
                  <DroneRow
                    key={u.id}
                    uav={u}
                    selected={targetingDroneId === u.id}
                    onSelect={onSelect}
                    locale={locale}
                  />
                ))}
              </div>
            </div>
          )
        })}
        {fleet.length === 0 && (
          <div className="text-xs italic" style={{ color: '#7A8BA3' }}>
            {locale === 'bm' ? 'Menunggu sambungan...' : 'Waiting for connection…'}
          </div>
        )}
      </div>
    </div>
  )
}
