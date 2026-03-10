import React, { useState, useEffect } from 'react'
import { hideData, extractData } from '../api'

export default function ShadowPixelForm({ file }) {
    const [mode, setMode] = useState('hide') // 'hide' or 'extract'
    const [message, setMessage] = useState('')
    const [password, setPassword] = useState('')
    const [psnr, setPsnr] = useState(null)
    const [extractedMsg, setExtractedMsg] = useState('')
    const [loading, setLoading] = useState(false)
    const [resultUrl, setResultUrl] = useState(null)
    const [embedImageFile, setEmbedImageFile] = useState(null)
    const [embeddedImageUrl, setEmbeddedImageUrl] = useState(null)
    const [embedPreviewUrl, setEmbedPreviewUrl] = useState(null)

    useEffect(() => {
        if (!embedImageFile) {
            if (embedPreviewUrl) {
                URL.revokeObjectURL(embedPreviewUrl)
                setEmbedPreviewUrl(null)
            }
            return
        }
        const u = URL.createObjectURL(embedImageFile)
        setEmbedPreviewUrl(u)
        return () => { URL.revokeObjectURL(u) }
    }, [embedImageFile])

    const onHide = async () => {
        if (!file || !password) return alert('กรุณาระบุรหัสผ่านและ ไฟล์หรือข้อความที่ต้องการซ่อน')
        if (!message && !embedImageFile) return alert('ต้องใส่ข้อความหรือไฟล์รูปสำหรับฝัง')
        setLoading(true)
        try {
            const { blob, psnr: psnrValue } = await hideData({ file, message, password, embedImage: embedImageFile })
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
        if (!file || !password) return alert('กรุณาระบุรหัสผ่านและ ไฟล์')
        setLoading(true)
        setExtractedMsg('')
        setEmbeddedImageUrl(null)
        try {
            const res = await extractData({ file, password })
            // if the backend returned an embedded image (data URL), show it
            if (res.embedded_image) {
                setEmbeddedImageUrl(res.embedded_image)
            }
            if (res.message) setExtractedMsg(res.message)
            if (res.extra_text) setExtractedMsg((res.message || '') + '\n' + (Array.isArray(res.extra_text) ? res.extra_text.join('\n') : res.extra_text))
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
                    <div className="row">
                        <label>ฝังรูป</label>
                        <div className="logo-file-input">
                            <label className="logo-file-button">
                                เลือกไฟล์
                                <input type="file" accept="image/*" onChange={(e) => setEmbedImageFile(e.target.files[0] || null)} />
                            </label>
                            {embedPreviewUrl && (
                                <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <img src={embedPreviewUrl} alt="embed preview" style={{ height: 56, borderRadius: 6, cursor: 'zoom-in' }} />
                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                        <div className="small filename">{embedImageFile && embedImageFile.name}</div>
                                        <button className="secondary" style={{ marginTop: 6 }} onClick={() => { setEmbedImageFile(null); if (embedPreviewUrl) { URL.revokeObjectURL(embedPreviewUrl); setEmbedPreviewUrl(null) } }}>Remove</button>
                                    </div>
                                </div>
                            )}
                            <span className="logo-file-name">{embedImageFile ? embedImageFile.name : 'ยังไม่ได้เลือกไฟล์'}</span>
                        </div>
                    </div>
                    <button className="preview" onClick={onHide} disabled={loading || !file}>
                        {loading ? 'กำลังประมวลผล...' : 'ซ่อนข้อมูลลงในภาพ'}
                    </button>

                    {resultUrl && (
                        <div className="result-area">
                            <h3>สำเร็จ! (Stego Image)</h3>
                            <p className="small">คุณภาพของภาพ (PSNR): <strong style={{ color: psnr > 40 ? '#4caf50' : '#ff9800' }}>{psnr} dB</strong></p>
                            <div className="preview-block">
                                <img src={resultUrl} alt="stego result" className="preview-image" />
                            </div>
                            <div style={{ marginTop: 10 }}>
                                <a href={resultUrl} download={`shadow-${file.name}`} className="button preview">ดาวน์โหลดภาพ</a>
                            </div>
                        </div>
                    )}
                    {embeddedImageUrl && (
                        <div className="result-area">
                            <h4>รูปที่ถูกฝัง (ใน payload)</h4>
                            <div className="preview-block">
                                <img src={embeddedImageUrl} alt="embedded" className="preview-image" />
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
                        <div className="result-area">
                            <h3 className="success">🔓 ถอดรหัสสำเร็จ!</h3>
                            <div className="extracted-block">
                                <div className="mono" style={{ whiteSpace: 'pre-wrap' }}>{extractedMsg}</div>
                                <div style={{ marginTop: 12 }}>
                                    <button className="secondary" onClick={() => { navigator.clipboard.writeText(extractedMsg); alert('คัดลอกลง Clipboard แล้ว!') }}>📋 คัดลอกข้อความ</button>
                                </div>
                            </div>
                        </div>
                    )}
                    {embeddedImageUrl && (
                        <div className="result-area">
                            <h4>รูปที่ถูกฝัง (ถูกดึงออก)</h4>
                            <div className="preview-block">
                                <img src={embeddedImageUrl} alt="embedded" className="preview-image" />
                            </div>
                            <div style={{ marginTop: 8 }}>
                                <a href={embeddedImageUrl} download={`embedded-${file.name}`} className="button preview">ดาวน์โหลดรูปที่ฝัง</a>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
