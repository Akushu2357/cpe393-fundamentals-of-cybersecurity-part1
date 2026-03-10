import React, { useState } from 'react'
import UploadPreview from './components/UploadPreview'
import WatermarkForm from './components/WatermarkForm'
import RemoveWatermarkForm from './components/RemoveWatermarkForm'
import ShadowPixelForm from './components/ShadowPixelForm'

export default function App() {
  const [mode, setMode] = useState('create') // 'create' or 'remove'
  const [file, setFile] = useState(null)

  return (
    <div className="app">
      <header>
        <div>
          <h1>Watermark Studio</h1>
          <p className="small">อัปโหลดไฟล์ ดูตัวอย่าง และใส่/ถอดลายน้ำได้อย่างรวดเร็ว (mock)</p>
        </div>

        <div className="mode-toggle">
          <button onClick={() => setMode('create')} className={mode === 'create' ? 'active' : ''}>Watermark (Visible)</button>
          <button onClick={() => setMode('remove')} className={mode === 'remove' ? 'active' : ''}>Remove Watermark</button>
          <button onClick={() => setMode('shadow')} className={mode === 'shadow' ? 'active' : 'stego-btn'}>Shadow-Pixel (Secret)</button>
        </div>
      </header>

      <main>
        <section className="left">
          <div className="card">
            <UploadPreview onFileSelected={setFile} file={file} />
          </div>
        </section>

        <section className="right">
          <div className="card">
            {mode === 'create' ? (
              <WatermarkForm file={file} />
            ) : mode === 'remove' ? (
              <RemoveWatermarkForm file={file} />
            ) : (
              <ShadowPixelForm file={file} />
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
