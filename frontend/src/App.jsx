import TacticalMap from './scene/TacticalMap'
import GlobalStatusBar from './panels/GlobalStatusBar'
import NarratorPanel from './components/NarratorPanel'
import GaugePanel from './components/GaugePanel'
import EventCard from './components/EventCard'
import StartScreen from './components/StartScreen'
import DebriefScreen from './components/DebriefScreen'
import useMissionStore from './stores/missionStore'
import useWebSocket from './hooks/useWebSocket'

export default function App() {
  useWebSocket()
  const gameStatus = useMissionStore(s => s.gameStatus)

  const showStart = gameStatus === 'not_started'
  const showDebrief = gameStatus === 'won' || gameStatus === 'partial' || gameStatus === 'failed'

  return (
    <div className="w-full h-full flex flex-col relative" style={{ background: '#0B1426' }}>
      <GlobalStatusBar />

      {/* Gauges strip — always visible once a game is active */}
      {!showStart && (
        <div className="shrink-0 border-b" style={{ borderColor: '#1E3A5F' }}>
          <GaugePanel />
        </div>
      )}

      <div className="flex-1 flex overflow-hidden relative">
        {/* Center: 3D tactical map */}
        <div className="flex-1 relative min-w-0 min-h-0">
          <TacticalMap />
          {/* Event card overlays the map when one is active */}
          <EventCard />
        </div>

        {/* Right sidebar: narrator log */}
        <div className="shrink-0 flex flex-col overflow-hidden" style={{ width: 320, maxWidth: '38vw', borderLeft: '1px solid #1E3A5F' }}>
          <NarratorPanel />
        </div>
      </div>

      {showStart && <StartScreen />}
      {showDebrief && <DebriefScreen />}
    </div>
  )
}
