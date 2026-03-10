import React, { useEffect, useState } from 'react'
import ImageLightbox from './ImageLightbox'
import { removeWatermark } from '../api'

export default function RemoveWatermarkForm({ file }) {
  const [previewUrl, setPreviewUrl] = useState(null)
  const [previewName, setPreviewName] = useState(null)
  const [lightboxSrc, setLightboxSrc] = useState(null)

  useEffect(() => {
    if (!file) {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
        setPreviewUrl(null)
        setPreviewName(null)
      }
      return
    }
    // initially show original file as preview
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    setPreviewName(`removed-${file.name}`)
    return () => {
      if (url) URL.revokeObjectURL(url)
    }
  }, [file])

  const onDownload = async () => {
    if (!file) return
    try {
      const blob = await removeWatermark({ file })
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      const url = URL.createObjectURL(blob)
      setPreviewUrl(url)
      setPreviewName(`removed-${file.name}`)
      const a = document.createElement('a')
      a.href = url
      a.download = `removed-${file.name}`
      a.click()
    } catch (err) {
      console.error(err)
      alert('เกิดข้อผิดพลาดขณะเรียก API: ' + err.message)
    }
  }

  return (
    <div className="form">
      <h2>ถอดลายน้ำ (Mock)</h2>
      <p>ฟีเจอร์ถอดลายน้ำยังเป็น mock — แสดงตัวอย่างไฟล์ต้นฉบับ และดาวน์โหลดเป็นตัวอย่าง</p>
      <div className="row">
        <button className="preview" onClick={onDownload} disabled={!previewUrl}>ดาวน์โหลดไฟล์ตัวอย่าง (Mock)</button>
      </div>

      {previewUrl && file && (
        <div className="row" style={{marginTop:8}}>
          <strong>Preview:</strong>
          {file.type && file.type.startsWith('image/') && (
            <img src={previewUrl} alt="preview" style={{maxWidth:'100%', marginTop:8, cursor:'zoom-in'}} onClick={() => setLightboxSrc(previewUrl)} />
          )}
          {file.type === 'application/pdf' && (
            <object data={previewUrl} type="application/pdf" width="100%" height="400">Preview not available</object>
          )}
          {lightboxSrc && <ImageLightbox src={lightboxSrc} onClose={() => setLightboxSrc(null)} />}
        </div>
      )}
    </div>
  )
}
