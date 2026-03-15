# CPE393 — Fundamentals of Cybersecurity (Part 1)

This repository is a small teaching/example project for the course "Fundamentals of Cybersecurity — Part 1". It contains a minimal FastAPI backend and a React (Vite) frontend demonstrating visible watermarking and a simple steganography feature.

Contents
- `backend/` — Python FastAPI mock server and processing helpers
- `frontend/` — React + Vite frontend client
- `image/` — sample images

Prerequisites
- Python 3.10+ (for the backend)
- Node.js 16+ and npm or yarn (for the frontend)

Quick start (two terminals)

Backend (terminal A):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1    # PowerShell
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 4000
```

Frontend (terminal B):

```bash
cd frontend
npm install
npm run dev
```

After both servers are running, open the URL reported by Vite (usually http://localhost:5173).

Important files
- `backend/app.py` — FastAPI application and endpoints
- `backend/shadow_pixel.py` — cryptography + steganography helpers (`ShadowCrypto`, `ShadowStego`)
- `frontend/src/api.js` — client API functions and `VITE_API_BASE` setting

Note: The frontend defaults `VITE_API_BASE` to `http://localhost:4000` in `frontend/src/api.js`. The backend example runs on port `4000` by default.

If you want, I can run the servers to verify or expand these READMEs with endpoint examples.