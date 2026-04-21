import { useMemo } from 'react'
import * as THREE from 'three'
import useMissionStore from '../stores/missionStore'
import { manualDispatch } from '../hooks/useGameApi'

// An invisible plane covering the full 20×20 grid. Only consumes clicks
// when the player has a drone selected (targetingDroneId is set).
export default function TargetingLayer() {
  const gridSize = useMissionStore(s => s.gridSize) || 20
  const targetingDroneId = useMissionStore(s => s.targetingDroneId)
  const setTargetingDroneId = useMissionStore(s => s.setTargetingDroneId)

  const geometry = useMemo(() => new THREE.PlaneGeometry(gridSize, gridSize), [gridSize])

  if (!targetingDroneId) return null

  const onClick = async (e) => {
    e.stopPropagation()
    const x = Math.round(e.point.x)
    const y = Math.round(e.point.z)
    if (x < 0 || x >= gridSize || y < 0 || y >= gridSize) return
    const droneId = targetingDroneId
    setTargetingDroneId(null)
    try {
      await manualDispatch(droneId, x, y)
    } catch (err) {
      console.error('[manualDispatch]', err)
    }
  }

  return (
    <mesh
      rotation={[-Math.PI / 2, 0, 0]}
      position={[(gridSize - 1) / 2, 0.02, (gridSize - 1) / 2]}
      geometry={geometry}
      onClick={onClick}
      onPointerOver={() => { document.body.style.cursor = 'crosshair' }}
      onPointerOut={() => { document.body.style.cursor = 'auto' }}
    >
      <meshBasicMaterial color="#FFCC00" transparent opacity={0.04} side={THREE.DoubleSide} />
    </mesh>
  )
}
