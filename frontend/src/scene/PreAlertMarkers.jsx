import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Billboard, Text } from '@react-three/drei'
import * as THREE from 'three'
import useMissionStore from '../stores/missionStore'

// Pulsing red hotspot painted at the coord of each upcoming card.
// Appears ~12 s before the call comes in. Scouting this cell with a
// drone gives the player advance intel — converting the map from
// decorative to "act early or absorb the surprise".
function PulsingPin({ coord, title }) {
  const ref = useRef(null)
  useFrame(({ clock }) => {
    if (ref.current) {
      const s = 0.85 + 0.25 * Math.sin(clock.elapsedTime * 4)
      ref.current.scale.set(s, s, s)
    }
  })
  const [x, y] = coord
  return (
    <group position={[x, 0.6, y]}>
      <mesh ref={ref}>
        <ringGeometry args={[0.45, 0.7, 48]} />
        <meshBasicMaterial color="#FF3A5C" transparent opacity={0.75} side={THREE.DoubleSide} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.3, 0]}>
        <ringGeometry args={[0.25, 0.45, 32]} />
        <meshBasicMaterial color="#FF3A5C" transparent opacity={0.4} side={THREE.DoubleSide} />
      </mesh>
      <Billboard position={[0, 1.1, 0]} follow>
        <Text fontSize={0.26} color="#FF3A5C" anchorY="bottom" outlineColor="#000" outlineWidth={0.02}>
          🚨 {title || 'Incoming call'}
        </Text>
      </Billboard>
    </group>
  )
}

export default function PreAlertMarkers() {
  const prealerts = useMissionStore(s => s.prealerts)
  const locale = useMissionStore(s => s.locale)
  const entries = Object.values(prealerts || {})
  if (entries.length === 0) return null
  return (
    <group>
      {entries.map(p => (
        <PulsingPin
          key={p.card_id}
          coord={p.coord}
          title={locale === 'bm' ? p.title_bm : p.title_en}
        />
      ))}
    </group>
  )
}
