import React, { useCallback, useState, useRef, useEffect } from 'react'
import PDFViewer from './PDFViewer'
import ImageLightbox from './ImageLightbox'

export default function UploadPreview({ onFileSelected, file }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()
  const [lightboxSrc, setLightboxSrc] = useState(null)

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files && e.dataTransfer.files[0]
    if (f) onFileSelected(f)
  }, [onFileSelected])

  useEffect(() => {
    const prevent = (e) => e.preventDefault()
    window.addEventListener('dragover', prevent)
    window.addEventListener('drop', prevent)
    return () => {
      window.removeEventListener('dragover', prevent)
      window.removeEventListener('drop', prevent)
    }
  }, [])

  return (
    <div className="upload-preview">
      {
        !file
          ? <div
            className={`dropzone ${dragging ? 'dragging' : ''}`}
            onDragEnter={() => setDragging(true)}
            onDragLeave={() => setDragging(false)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={onDrop}
            onClick={() => inputRef.current.click()}
          >
            <p>ลากไฟล์มาที่นี่ หรือ คลิกเพื่อเลือกไฟล์</p>
            <input
              ref={inputRef}
              type="file"
              style={{ display: 'none' }}
              onChange={(e) => onFileSelected(e.target.files[0])}
              accept="image/*,application/pdf"
            />
          </div>
          : <div className="preview-area">
              <div className="preview-card">
                <div className="file-meta">
                  <div>
                    <div className="filename">{file.name}</div>
                    <div className="small muted">{Math.round(file.size / 1024)} KB • {file.type}</div>
                  </div>
                  <div>
                    <button className="secondary" onClick={() => onFileSelected(null)}>เปลี่ยน</button>
                  </div>
                </div>

                <div style={{ width: '100%', marginTop: 10 }}>
                  {file.type.startsWith('image/') && (
                    <img src={URL.createObjectURL(file)} alt="preview" style={{ cursor: 'zoom-in' }} onClick={() => setLightboxSrc(URL.createObjectURL(file))} />
                  )}
                  {file.type === 'application/pdf' && (
                    <PDFViewer file={file} />
                  )}
                  {lightboxSrc && (
                    <ImageLightbox src={lightboxSrc} onClose={() => { URL.revokeObjectURL(lightboxSrc); setLightboxSrc(null) }} />
                  )}
                </div>
              </div>
          </div>
      }
    </div>
  )
}
