import React, { useState, useEffect } from 'react'
import ImageLightbox from './ImageLightbox'
import CustomSelect from './CustomSelect'
import { createWatermark } from '../api'

function downloadUrl(url, filename) {
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
}

export default function WatermarkForm({ file }) {
  const [type, setType] = useState('text') // text or image
  const [text, setText] = useState('SAMPLE')
  const [pos, setPos] = useState('center')
  const [opacity, setOpacity] = useState(0.4)
  const [logoFile, setLogoFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [previewName, setPreviewName] = useState(null)
  const [lightboxSrc, setLightboxSrc] = useState(null)
  const [logoPreviewUrl, setLogoPreviewUrl] = useState(null)

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      if (logoPreviewUrl) URL.revokeObjectURL(logoPreviewUrl)
    }
  }, [previewUrl])

  useEffect(() => {
    if (!logoFile) {
      if (logoPreviewUrl) {
        URL.revokeObjectURL(logoPreviewUrl)
        setLogoPreviewUrl(null)
      }
      return
    }
    const u = URL.createObjectURL(logoFile)
    setLogoPreviewUrl(u)
    return () => {
      if (u) URL.revokeObjectURL(u)
    }
  }, [logoFile])

  const setPreviewFromBlob = (blob, filename) => {
    if (!blob) return
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    const url = URL.createObjectURL(blob)
    setPreviewUrl(url)
    setPreviewName(filename)
  }

  const applyToImage = async () => {
    if (!file || !file.type.startsWith('image/')) return alert('กรุณาอัปโหลดภาพก่อน')
    const img = new Image()
    img.src = URL.createObjectURL(file)
    await img.decode()
    const canvas = document.createElement('canvas')
    canvas.width = img.naturalWidth
    canvas.height = img.naturalHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, 0, 0)

    ctx.globalAlpha = opacity
    ctx.fillStyle = 'white'
    ctx.textBaseline = 'middle'
    const fontSize = Math.max(20, Math.floor(canvas.width / 15))
    ctx.font = `${fontSize}px sans-serif`

    let x = canvas.width / 2
    let y = canvas.height / 2
    if (pos === 'top-left') { x = 50; y = 50 }
    if (pos === 'bottom-right') { x = canvas.width - 50; y = canvas.height - 50 }

    if (type === 'text') {
      ctx.textAlign = 'center'
      ctx.fillText(text, x, y)
    } else if (type === 'image' && logoFile) {
      const logo = new Image()
      logo.src = URL.createObjectURL(logoFile)
      await logo.decode()
      const w = canvas.width * 0.25
      const h = (logo.naturalHeight / logo.naturalWidth) * w
      const lx = pos === 'bottom-right' ? canvas.width - w - 30 : x - w / 2
      const ly = pos === 'top-left' ? 30 : y - h / 2
      ctx.drawImage(logo, lx, ly, w, h)
    }

    return new Promise((res) => {
      canvas.toBlob((b) => {
        setPreviewFromBlob(b, `watermarked-${file.name}`)
        res()
      }, file.type)
    })
  }

  const applyToPdfFirstPage = async () => {
    if (!file || file.type !== 'application/pdf') return alert('กรุณาอัปโหลด PDF ก่อน')
    const { getDocument, GlobalWorkerOptions } = await import('pdfjs-dist/legacy/build/pdf')
    GlobalWorkerOptions.workerSrc = 'https://unpkg.com/pdfjs-dist@3.9.179/build/pdf.worker.min.js'
    const array = await file.arrayBuffer()
    const pdf = await getDocument({ data: array }).promise
    const page = await pdf.getPage(1)
    const viewport = page.getViewport({ scale: 2 })
    const canvas = document.createElement('canvas')
    canvas.width = viewport.width
    canvas.height = viewport.height
    const ctx = canvas.getContext('2d')
    await page.render({ canvasContext: ctx, viewport }).promise

    ctx.globalAlpha = opacity
    ctx.fillStyle = 'white'
    ctx.textBaseline = 'middle'
    const fontSize = Math.max(20, Math.floor(canvas.width / 15))
    ctx.font = `${fontSize}px sans-serif`
    ctx.textAlign = 'center'
    ctx.fillText(text, canvas.width / 2, canvas.height / 2)

    return new Promise((res) => {
      canvas.toBlob((b) => {
        setPreviewFromBlob(b, `watermarked-${file.name.replace('.pdf', '')}.png`)
        res()
      }, 'image/png')
    })
  }

  const onApply = async () => {
    if (!file) return alert('กรุณาอัปโหลดไฟล์ก่อน')
    try {
      // call backend mock
      const blob = await createWatermark({ file, type, text, pos, opacity, logo: logoFile })
      setPreviewFromBlob(blob, `watermarked-${file.name}`)
    } catch (err) {
      console.error(err)
      alert('เกิดข้อผิดพลาดขณะเรียก API: ' + err.message)
    }
  }

  const onDownloadPreview = () => {
    if (!previewUrl || !previewName) return
    downloadUrl(previewUrl, previewName)
  }

  return (
    <div className="form">
      <h2>สร้างลายน้ำ (Mock)</h2>
      <div className="row">
        <label>ประเภทลายน้ำ</label>
        <CustomSelect
          value={type}
          onChange={setType}
          options={[
            { value: 'text', label: 'ข้อความ' },
            { value: 'image', label: 'รูปภาพ' }
          ]}
        />
      </div>

      {type === 'text' && (
        <div className="row">
          <label>ข้อความ</label>
          <input type="text" value={text} onChange={(e) => setText(e.target.value)} />
        </div>
      )}

      {type === 'image' && (
        <div className="row">
          <label>อัปโหลดโลโก้</label>
          <div className="logo-file-input">
            <label className="logo-file-button">
              เลือกไฟล์
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setLogoFile(e.target.files[0] || null)}
              />
            </label>
            <span className="logo-file-name">{logoFile ? logoFile.name : 'ยังไม่ได้เลือกไฟล์'}</span>
          </div>
          {logoPreviewUrl && (
            <div style={{marginTop:8, display:'flex', alignItems:'center', gap:8}}>
              <img src={logoPreviewUrl} alt="logo preview" style={{height:56, borderRadius:6, cursor:'zoom-in'}} onClick={() => setLightboxSrc(logoPreviewUrl)} />
              <div style={{display:'flex',flexDirection:'column'}}>
                <div className="small filename">{logoFile && logoFile.name}</div>
                <button className="secondary" style={{marginTop:6}} onClick={() => { setLogoFile(null); if (logoPreviewUrl) { URL.revokeObjectURL(logoPreviewUrl); setLogoPreviewUrl(null) } }}>Remove</button>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="row">
        <label>ตำแหน่ง</label>
        <CustomSelect
          value={pos}
          onChange={setPos}
          options={[
            { value: 'top-left', label: 'มุมบนซ้าย' },
            { value: 'center', label: 'กึ่งกลาง' },
            { value: 'bottom-right', label: 'มุมล่างขวา' }
          ]}
        />
      </div>

      <div className="row">
        <label>ความทึบ: {Math.round(opacity * 100)}%</label>
        <input type="range" min="0" max="1" step="0.05" value={opacity} onChange={(e) => setOpacity(parseFloat(e.target.value))} />
      </div>

      <div className="row">
        <button className="preview" onClick={onApply} disabled={!file}>Generate Preview</button>
        {previewUrl && (
          <>
            <div style={{marginTop:8}}>
              <strong>Preview:</strong>
            </div>
            <div style={{marginTop:8}}>
              <img src={previewUrl} alt="preview" style={{maxWidth: '100%', cursor:'zoom-in'}} onClick={() => setLightboxSrc(previewUrl)} />
            </div>
            <div style={{marginTop:8}}>
              <button className='preview' onClick={onDownloadPreview}>Download</button>
            </div>
            {lightboxSrc && <ImageLightbox src={lightboxSrc} onClose={() => setLightboxSrc(null)} />}
          </>
        )}
      </div>
    </div>
  )
}
