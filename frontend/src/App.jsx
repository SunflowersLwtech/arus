import { useEffect, useState } from 'react'
import TacticalMap from './scene/TacticalMap'
import GlobalStatusBar from './panels/GlobalStatusBar'
import NarratorPanel from './components/NarratorPanel'
import GaugePanel from './components/GaugePanel'
import EventCard from './components/EventCard'
import StartScreen from './components/StartScreen'
import DebriefScreen from './components/DebriefScreen'
import AgencyStatusPanel from './components/AgencyStatusPanel'
import NextCallEta from './components/NextCallEta'
import CoachConsole from './components/CoachConsole'
import AutoWatcher from './components/AutoWatcher'
import useMissionStore from './stores/missionStore'
import useWebSocket from './hooks/useWebSocket'

function useIsNarrow(threshold = 900) {
  const [narrow, setNarrow] = useState(
    typeof window !== 'undefined' && window.innerWidth < threshold,
  )
  useEffect(() => {
    const handler = () => setNarrow(window.innerWidth < threshold)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [threshold])
  return narrow
}

function MobileDrawer({ side, open, onClose, children }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40" onClick={onClose}>
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.5)' }} />
      <div
        onClick={e => e.stopPropagation()}
        className="absolute top-0 bottom-0 flex flex-col"
        style={{
          [side]: 0,
          width: 'min(320px, 88vw)',
          background: '#0F1C33',
          boxShadow: '0 0 40px rgba(0,0,0,0.7)',
        }}
      >
        {children}
      </div>
    </div>
  )
}

export default function App() {
  useWebSocket()
  const gameStatus = useMissionStore(s => s.gameStatus)
  const mode = useMissionStore(s => s.mode)
  const narrow = useIsNarrow()
  const [leftOpen, setLeftOpen] = useState(false)
  const [rightOpen, setRightOpen] = useState(false)

  const showStart = gameStatus === 'not_started'
  const showDebrief = gameStatus === 'won' || gameStatus === 'partial' || gameStatus === 'failed'

  // Per-mode right-panel selection.
  const RightPanel = mode === 'COACH' ? CoachConsole : mode === 'AUTO' ? AutoWatcher : NarratorPanel

  return (
    <div className="w-full h-full flex flex-col relative" style={{ background: '#0B1426' }}>
      <GlobalStatusBar />

      {!showStart && mode !== 'AUTO' && (
        <div className="shrink-0 border-b" style={{ borderColor: '#1E3A5F' }}>
          <GaugePanel />
        </div>
      )}

      <div className="flex-1 flex overflow-hidden relative">
        {/* Left sidebar (desktop) / drawer (mobile) — hidden in AUTO */}
        {!showStart && mode !== 'AUTO' && !narrow && (
          <div className="shrink-0 flex flex-col overflow-hidden" style={{ width: 240, maxWidth: '30vw', borderRight: '1px solid #1E3A5F' }}>
            <AgencyStatusPanel />
          </div>
        )}
        {!showStart && mode !== 'AUTO' && narrow && (
          <MobileDrawer side="left" open={leftOpen} onClose={() => setLeftOpen(false)}>
            <AgencyStatusPanel />
          </MobileDrawer>
        )}

        {/* Center: 3D tactical map */}
        <div className="flex-1 relative min-w-0 min-h-0">
          <TacticalMap />
          <NextCallEta />
          <EventCard />

          {/* Mobile drawer trigger buttons — only on narrow viewports, while game active */}
          {!showStart && narrow && (
            <>
              {mode !== 'AUTO' && (
                <button
                  onClick={() => setLeftOpen(true)}
                  className="absolute top-3 left-3 z-20 px-3 py-1.5 rounded-full text-[11px] font-mono font-semibold shadow-lg"
                  style={{ background: 'rgba(15,28,51,0.9)', color: '#00D4FF', border: '1px solid #00D4FF80' }}
                >
                  ✈ Agencies
                </button>
              )}
              <button
                onClick={() => setRightOpen(true)}
                className="absolute bottom-3 right-3 z-20 px-3 py-1.5 rounded-full text-[11px] font-mono font-semibold shadow-lg"
                style={{ background: 'rgba(15,28,51,0.9)', color: '#FFCC00', border: '1px solid #FFCC0080' }}
              >
                {mode === 'COACH' ? '🧠 AI' : mode === 'AUTO' ? '🎛 ADK' : '📻 Radio'}
              </button>
            </>
          )}
        </div>

        {/* Right sidebar (desktop) / drawer (mobile) */}
        {!showStart && !narrow && (
          <div className="shrink-0 flex flex-col overflow-hidden" style={{ width: 320, maxWidth: '38vw', borderLeft: '1px solid #1E3A5F' }}>
            <RightPanel />
          </div>
        )}
        {!showStart && narrow && (
          <MobileDrawer side="right" open={rightOpen} onClose={() => setRightOpen(false)}>
            <RightPanel />
          </MobileDrawer>
        )}
      </div>

      {showStart && <StartScreen />}
      {showDebrief && <DebriefScreen />}
    </div>
  )
}
