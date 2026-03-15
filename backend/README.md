# Backend (FastAPI)

Minimal FastAPI backend that provides example endpoints for watermarking and a simple steganography (shadow-pixel) workflow.

Key files
- `requirements.txt` — Python dependencies
- `app.py` — FastAPI application and endpoint implementations
- `shadow_pixel.py` — `ShadowCrypto` (AES-256-GCM + scrypt) and `ShadowStego` (permutation-based LSB steganography)

Main endpoints (see `app.py` for full details):
- `GET /` — health/status
- `POST /api/watermark/create` — Upload a file and apply a visible watermark. Accepts form fields: `type` (`text` or `image`), `text`, `pos`, `opacity`, and optional `logo` for image-watermarking. Images return a JPEG; other files are echoed back as a mock behavior.
- `POST /api/watermark/remove` — Upload a file and receive a mocked "removed" file as a response.
- `POST /api/stego/hide` — Embed data into an image. Form fields: `file` (image), `message` (optional), `password` (required), `embed_image` (optional). Returns a PNG stego image and `X-PSNR` header.
- `POST /api/stego/extract` — Extract hidden payload from an image using `password`. Returns JSON with `message` and/or `embedded_image` (data URL) when present.

Quick start (Python 3.10+ recommended):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1    # PowerShell
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 4000
```

To point the frontend to this backend, set `VITE_API_BASE` to `http://localhost:4000` or update `frontend/src/api.js` accordingly.
