const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:4000'

export async function createWatermark({ file, type, text, pos, opacity, logo }) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('type', type)
  if (text) fd.append('text', text)
  if (pos) fd.append('pos', pos)
  if (opacity != null) fd.append('opacity', String(opacity))
  if (logo) fd.append('logo', logo)

  const res = await fetch(`${API_BASE}/api/watermark/create`, {
    method: 'POST',
    body: fd,
  })
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(txt || 'Server error')
  }
  const blob = await res.blob()
  return blob
}

export async function removeWatermark({ file }) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${API_BASE}/api/watermark/remove`, {
    method: 'POST',
    body: fd,
  })
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(txt || 'Server error')
  }
  const blob = await res.blob()
  return blob
}

export async function hideData({ file, message, password }) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('message', message)
  fd.append('password', password)

  const res = await fetch(`${API_BASE}/api/stego/hide`, {
    method: 'POST',
    body: fd,
  })
  if (!res.ok) {
    const txt = await res.json()
    throw new Error(txt.error || 'Server error')
  }
  const psnr = res.headers.get('X-PSNR')
  const blob = await res.blob()
  return { blob, psnr }
}

export async function extractData({ file, password }) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('password', password)

  const res = await fetch(`${API_BASE}/api/stego/extract`, {
    method: 'POST',
    body: fd,
  })
  if (!res.ok) {
    const txt = await res.json()
    throw new Error(txt.error || 'Server error')
  }
  return await res.json()
}
