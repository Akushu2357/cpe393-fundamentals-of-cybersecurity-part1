import React, { useEffect, useState, useRef } from 'react'

export default function ImageLightbox({ src, onClose }) {
  const [scale, setScale] = useState(1)
  const containerRef = useRef(null)

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
      if (e.key === '+') setScale((s) => Math.min(5, s + 0.25))
      if (e.key === '-') setScale((s) => Math.max(0.25, s - 0.25))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    const wheel = (e) => {
      if (!e.ctrlKey) return
      e.preventDefault()
      const delta = e.deltaY > 0 ? -0.1 : 0.1
      setScale((s) => Math.max(0.25, Math.min(5, +(s + delta).toFixed(2))))
    }
    const node = containerRef.current
    node && node.addEventListener('wheel', wheel, { passive: false })
    return () => node && node.removeEventListener('wheel', wheel)
  }, [])

  return (
    <div className="lightbox-overlay" onClick={onClose}>
      <div className="lightbox-inner" onClick={(e) => e.stopPropagation()} ref={containerRef}>
        <div className="lightbox-toolbar">
          <button onClick={onClose} className="secondary">Close</button>
          <div style={{flex:1}} />
          <button onClick={() => setScale((s) => Math.max(0.25, +(s - 0.25).toFixed(2)))} className="secondary">-</button>
          <button onClick={() => setScale((s) => Math.min(5, +(s + 0.25).toFixed(2)))} style={{marginLeft:8}}>+</button>
        </div>

        <div className="lightbox-canvas">
          <img src={src} alt="lightbox" style={{transform: `scale(${scale})`}} />
        </div>
      </div>
    </div>
  )
}
