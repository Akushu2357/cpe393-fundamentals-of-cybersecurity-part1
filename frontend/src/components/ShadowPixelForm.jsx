import React, { useState } from 'react'
import { hideData, extractData } from '../api'

export default function ShadowPixelForm({ file }) {
    const [mode, setMode] = useState('hide') // 'hide' or 'extract'
    const [message, setMessage] = useState('')
    const [password, setPassword] = useState('')
    const [psnr, setPsnr] = useState(null)
    const [extractedMsg, setExtractedMsg] = useState('')
    const [loading, setLoading] = useState(false)
    const [resultUrl, setResultUrl] = useState(null)

    const onHide = async () => {
        if (!file || !password || !message) return alert('กรุณาระบุไฟล์ ข้อความ และรหัสผ่าน')
        setLoading(true)
        try {
            const { blob, psnr: psnrValue } = await hideData({ file, message, password })
            const url = URL.createObjectURL(blob)
            setResultUrl(url)
            setPsnr(psnrValue)
        } catch (err) {
            alert('Error: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    const onExtract = async () => {
        if (!file || !password) return alert('กรุณาระบุไฟล์และรหัสผ่าน')
        setLoading(true)
        setExtractedMsg('')
        try {
            const res = await extractData({ file, password })
            setExtractedMsg(res.message)
        } catch (err) {
            alert('Error: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="form shadow-pixel-form">
            <h2>Project: Shadow-Pixel</h2>
            <div className="mode-toggle sub-toggle">
                <button onClick={() => setMode('hide')} className={mode === 'hide' ? 'active' : ''}>ซ่อนข้อมูล (Hide)</button>
                <button onClick={() => setMode('extract')} className={mode === 'extract' ? 'active' : ''}>ดึงข้อมูล (Extract)</button>
            </div>

            <div className="row">
                <label>รหัสผ่าน (Encryption Key & Seed)</label>
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="รหัสผ่านสำหรับรหัสและสุ่มพิกเซล"
                />
            </div>

            {mode === 'hide' ? (
                <>
                    <div className="row">
                        <label>ข้อความลับที่ต้องการซ่อน</label>
                        <textarea
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="พิมพ์ข้อความที่นี่..."
                            rows={4}
                        />
                    </div>
                    <button className="preview" onClick={onHide} disabled={loading || !file}>
                        {loading ? 'กำลังประมวลผล...' : 'ซ่อนข้อมูลลงในภาพ'}
                    </button>

                    {resultUrl && (
                        <div className="result-area" style={{ marginTop: 20 }}>
                            <h3>สำเร็จ! (Stego Image)</h3>
                            <p className="small">คุณภาพของภาพ (PSNR): <span style={{ color: psnr > 40 ? '#4caf50' : '#ff9800' }}>{psnr} dB</span></p>
                            <img src={resultUrl} alt="stego result" style={{ maxWidth: '100%', borderRadius: 8 }} />
                            <div style={{ marginTop: 10 }}>
                                <a href={resultUrl} download={`shadow-${file.name}`} className="button preview" style={{ display: 'inline-block', textDecoration: 'none', textAlign: 'center' }}>ดาวน์โหลดภาพ</a>
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <>
                    <button className="preview" onClick={onExtract} disabled={loading || !file}>
                        {loading ? 'กำลังดึงข้อมูล...' : 'ถอดความลับออกมา'}
                    </button>
                    {extractedMsg && (
                        <div className="result-area" style={{
                            marginTop: 20,
                            padding: 20,
                            background: '#1a1a1a',
                            borderRadius: 12,
                            border: '2px solid #4caf50',
                            boxShadow: '0 0 15px rgba(76, 175, 80, 0.2)'
                        }}>
                            <h3 style={{ color: '#4caf50', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span>🔓</span> ถอดรหัสสำเร็จ!
                            </h3>
                            <div style={{
                                padding: '15px',
                                background: '#000',
                                borderRadius: 8,
                                color: '#ffffff', // บังคับให้เป็นสีขาว
                                fontSize: '1.25rem',
                                fontWeight: '600',
                                wordBreak: 'break-all',
                                minHeight: '60px',
                                display: 'flex',
                                alignItems: 'center',
                                borderLeft: '4px solid #4caf50'
                            }}>
                                {extractedMsg}
                            </div>
                            <button
                                className="secondary"
                                style={{ marginTop: 15, background: '#333', color: '#fff' }}
                                onClick={() => { navigator.clipboard.writeText(extractedMsg); alert('คัดลอกลง Clipboard แล้ว!') }}
                            >
                                📋 คัดลอกข้อความ
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
