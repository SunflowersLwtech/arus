import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Billboard, Text } from '@react-three/drei'
import * as THREE from 'three'
import useMissionStore from '../stores/missionStore'

const _pos = new THREE.Vector3()

function bodyColor(uav) {
  if (uav.status === 'offline') return '#6C757D'
  if (uav.power <= 20) return '#E63946'
  return uav.agency_color || '#00D4FF'
}

function UAVLabel({ uav, selected }) {
  return (
    <Billboard position={[uav.x, 1.9, uav.y]} follow>
      <Text
        fontSize={0.32}
        color={selected ? '#FFCC00' : (uav.agency_color || '#00D4FF')}
        anchorY="bottom"
        font={undefined}
        outlineColor="#000"
        outlineWidth={0.02}
      >
        {uav.agency_short ? `${uav.agency_short} · ${uav.id}` : uav.id}
      </Text>
      <Text
        fontSize={0.2}
        color="rgba(255,255,255,0.7)"
        position={[0, -0.32, 0]}
        font={undefined}
        outlineColor="#000"
        outlineWidth={0.015}
      >
        {Math.round(uav.power)}% · {uav.status}
      </Text>
    </Billboard>
  )
}

export default function FleetRenderer() {
  const fleet = useMissionStore(state => state.fleet)
  const selectedDroneId = useMissionStore(state => state.targetingDroneId)
  const setTargetingDroneId = useMissionStore(state => state.setTargetingDroneId)
  const instanceRefs = useRef({})

  useFrame((_, delta) => {
    const currentFleet = useMissionStore.getState().fleet
    currentFleet.forEach(uav => {
      const ref = instanceRefs.current[uav.id]
      if (ref) {
        _pos.set(uav.x, 0.5, uav.y)
        ref.position.lerp(_pos, 1 - Math.exp(-8 * delta))
        ref.position.y = 0.5 + Math.sin(Date.now() * 0.003 + uav.x) * 0.05
      }
    })
  })

  const onDroneClick = (e, uav) => {
    e.stopPropagation()
    setTargetingDroneId(selectedDroneId === uav.id ? null : uav.id)
  }

  return (
    <group>
      {fleet.map(uav => {
        const color = bodyColor(uav)
        const selected = uav.id === selectedDroneId
        return (
          <group key={uav.id}>
            <group
              ref={el => { if (el) instanceRefs.current[uav.id] = el }}
              position={[uav.x, 0.5, uav.y]}
              onClick={(e) => onDroneClick(e, uav)}
              onPointerOver={(e) => { e.stopPropagation(); document.body.style.cursor = 'pointer' }}
              onPointerOut={() => { document.body.style.cursor = 'auto' }}
            >
              {/* Drone body */}
              <mesh>
                <octahedronGeometry args={[selected ? 0.35 : 0.27, 0]} />
                <meshStandardMaterial
                  color={color}
                  emissive={color}
                  emissiveIntensity={selected ? 1.0 : 0.6}
                  metalness={0.8}
                  roughness={0.2}
                />
              </mesh>
              {/* Selected halo */}
              {selected && (
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.35, 0]}>
                  <ringGeometry args={[0.6, 0.75, 48]} />
                  <meshBasicMaterial color="#FFCC00" transparent opacity={0.9} side={THREE.DoubleSide} />
                </mesh>
              )}
              {/* Sensor range ring */}
              <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.45, 0]}>
                <ringGeometry args={[uav.sensor_range - 0.1, uav.sensor_range, 32]} />
                <meshBasicMaterial color={color} transparent opacity={0.12} side={THREE.DoubleSide} />
              </mesh>
            </group>
            <UAVLabel uav={uav} selected={selected} />
          </group>
        )
      })}
    </group>
  )
}
