import React, { useEffect, useRef, useState } from 'react'
import { GlobalWorkerOptions, getDocument } from 'pdfjs-dist/legacy/build/pdf'

GlobalWorkerOptions.workerSrc = 'https://unpkg.com/pdfjs-dist@3.9.179/build/pdf.worker.min.js'

export default function PDFViewer({ file }) {
  const canvasRef = useRef(null)
  const [pdfDoc, setPdfDoc] = useState(null)
  const [page, setPage] = useState(1)
  const [numPages, setNumPages] = useState(0)

  useEffect(() => {
    if (!file) return
    const load = async () => {
      const array = await file.arrayBuffer()
      const loadingTask = getDocument({ data: array })
      const pdf = await loadingTask.promise
      setPdfDoc(pdf)
      setNumPages(pdf.numPages)
      setPage(1)
    }
    load().catch(console.error)
  }, [file])

  useEffect(() => {
    const renderPage = async () => {
      if (!pdfDoc) return
      const p = await pdfDoc.getPage(page)
      const viewport = p.getViewport({ scale: 1.5 })
      const canvas = canvasRef.current
      canvas.width = viewport.width
      canvas.height = viewport.height
      const ctx = canvas.getContext('2d')
      const renderContext = { canvasContext: ctx, viewport }
      await p.render(renderContext).promise
    }
    renderPage().catch(console.error)
  }, [pdfDoc, page])

  return (
    <div className="pdf-viewer">
      <div className="controls">
        <button onClick={() => setPage((s) => Math.max(1, s - 1))} disabled={page <= 1}>Prev</button>
        <span>หน้า {page} / {numPages || '...'}</span>
        <button onClick={() => setPage((s) => Math.min(numPages, s + 1))} disabled={page >= numPages}>Next</button>
      </div>
      <canvas ref={canvasRef} />
    </div>
  )
}
