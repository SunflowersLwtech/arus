import { useMemo } from 'react'
import * as THREE from 'three'
import { Billboard, Text, Line } from '@react-three/drei'
import useMissionStore from '../stores/missionStore'

// Render a semi-transparent "ghost" drone at the AI's suggested target +
// a dashed path from the actual drone. Appears only when COACH has a
// recommendation for the current card.
export default function GhostDrones() {
  const recommendation = useMissionStore(s => s.recommendation)
  const currentCard = useMissionStore(s => s.currentCard)
  const fleet = useMissionStore(s => s.fleet)
  const mode = useMissionStore(s => s.mode)

  const geom = useMemo(() => new THREE.OctahedronGeometry(0.3, 0), [])

  if (mode !== 'COACH' || !recommendation || !currentCard) return null
  if (!recommendation.card_id || recommendation.card_id !== currentCard.id) return null

  const target = currentCard.coord
  if (!Array.isArray(target) || target.length !== 2) return null

  const [tx, ty] = target
  const suggested = recommendation.suggested_drone
  const drone = fleet.find(u => u.id === suggested)
  const color = '#FFCC00'

  return (
    <group>
      {/* Ghost drone silhouette at target */}
      <group position={[tx, 0.9, ty]}>
        <mesh geometry={geom}>
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={0.8}
            transparent
            opacity={0.45}
          />
        </mesh>
        {/* pulsing ring */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.45, 0]}>
          <ringGeometry args={[0.6, 0.85, 48]} />
          <meshBasicMaterial color={color} transparent opacity={0.4} side={THREE.DoubleSide} />
        </mesh>
        <Billboard position={[0, 1.4, 0]} follow>
          <Text fontSize={0.28} color={color} anchorY="bottom" outlineColor="#000" outlineWidth={0.02}>
            {suggested ? `AI → ${suggested}` : 'AI suggests'}
          </Text>
        </Billboard>
      </group>

      {/* Dashed path from the actual drone to the suggested target */}
      {drone && (
        <Line
          points={[[drone.x, 0.8, drone.y], [tx, 0.8, ty]]}
          color={color}
          lineWidth={2}
          dashed
          dashSize={0.3}
          gapSize={0.25}
          transparent
          opacity={0.7}
        />
      )}
    </group>
  )
}
