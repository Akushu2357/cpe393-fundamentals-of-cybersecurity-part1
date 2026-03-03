const express = require('express')
const cors = require('cors')
const multer = require('multer')
const Jimp = require('jimp')

const app = express()
app.use(cors())

const upload = multer({ storage: multer.memoryStorage() })

app.get('/', (req, res) => res.json({ ok: true, msg: 'Watermark backend mock' }))

// Create watermark (mock)
// Accepts multipart/form-data: file (required), type (text|image), text, pos, opacity, optional logo
app.post('/api/watermark/create', upload.fields([{ name: 'file' }, { name: 'logo' }]), async (req, res) => {
  try {
    if (!req.files || !req.files.file || !req.files.file[0]) return res.status(400).json({ error: 'file required' })
    const file = req.files.file[0]
    const type = (req.body.type || 'text')
    const text = req.body.text || 'SAMPLE'
    const pos = req.body.pos || 'center'
    const opacity = parseFloat(req.body.opacity || '0.4')

    const mime = file.mimetype

    if (mime.startsWith('image/')) {
      const image = await Jimp.read(file.buffer)
      const w = image.bitmap.width
      const h = image.bitmap.height

      if (type === 'text') {
        const font = await Jimp.loadFont(Jimp.FONT_SANS_64_WHITE)
        const textImg = new Jimp(w, h, 0x00000000)
        textImg.print(font, 0, 0, {
          text,
          alignmentX: Jimp.HORIZONTAL_ALIGN_CENTER,
          alignmentY: Jimp.VERTICAL_ALIGN_MIDDLE
        }, w, h)
        textImg.opacity(opacity)
        image.composite(textImg, 0, 0)
      } else if (type === 'image' && req.files.logo && req.files.logo[0]) {
        const logo = await Jimp.read(req.files.logo[0].buffer)
        const lw = Math.floor(w * 0.22)
        const lh = Math.floor((logo.bitmap.height / logo.bitmap.width) * lw)
        logo.resize(lw, lh)
        logo.opacity(opacity)
        const lx = pos === 'bottom-right' ? w - lw - 24 : pos === 'top-left' ? 24 : Math.floor((w - lw) / 2)
        const ly = pos === 'bottom-right' ? h - lh - 24 : pos === 'top-left' ? 24 : Math.floor((h - lh) / 2)
        image.composite(logo, lx, ly)
      }

      const outBuffer = await image.getBufferAsync(mime)
      res.setHeader('Content-Type', mime)
      res.setHeader('Content-Disposition', `attachment; filename="watermarked-${file.originalname}"`)
      return res.send(outBuffer)
    }

    // For PDFs or unknown types: echo back the same file (mock)
    res.setHeader('Content-Type', mime)
    res.setHeader('Content-Disposition', `attachment; filename="watermarked-${file.originalname}"`)
    return res.send(file.buffer)
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: String(err) })
  }
})

// Remove watermark (mock) - just returns original file
app.post('/api/watermark/remove', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'file required' })
    const f = req.file
    res.setHeader('Content-Type', f.mimetype)
    res.setHeader('Content-Disposition', `attachment; filename="removed-${f.originalname}"`)
    return res.send(f.buffer)
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: String(err) })
  }
})

const PORT = process.env.PORT || 4000
app.listen(PORT, () => console.log(`Mock backend listening on http://localhost:${PORT}`))
