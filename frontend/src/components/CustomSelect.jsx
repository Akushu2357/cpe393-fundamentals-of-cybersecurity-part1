import React, { useEffect, useRef, useState } from 'react'

export default function CustomSelect({ value, onChange, options, placeholder = 'เลือก', disabled }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handleClick = (e) => {
      if (!ref.current) return
      if (!ref.current.contains(e.target)) setOpen(false)
    }
    const handleKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('click', handleClick)
    window.addEventListener('keydown', handleKey)
    return () => {
      window.removeEventListener('click', handleClick)
      window.removeEventListener('keydown', handleKey)
    }
  }, [])

  const current = options.find((o) => o.value === value)

  const handleSelect = (val) => {
    if (onChange) onChange(val)
    setOpen(false)
  }

  return (
    <div className={`custom-select ${disabled ? 'disabled' : ''}`} ref={ref}>
      <button
        type="button"
        className="custom-select-trigger"
        onClick={() => !disabled && setOpen((prev) => !prev)}
      >
        <span>{current ? current.label : placeholder}</span>
        <span className="chevron" />
      </button>
      {open && !disabled && (
        <div className="custom-select-menu">
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`custom-select-item ${opt.value === value ? 'active' : ''}`}
              onClick={() => handleSelect(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
