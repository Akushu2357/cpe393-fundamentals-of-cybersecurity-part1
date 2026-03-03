# FastAPI mock backend example

This folder contains a minimal FastAPI example that exposes the same mock endpoints as the Node mock server.

Files:
- `requirements.txt` — Python dependencies
- `app.py` — FastAPI app with endpoints:
  - `POST /api/watermark/create` — accepts `file`, `type`, `text`, `pos`, `opacity`, optional `logo`. For images it applies a simple watermark using Pillow and returns a JPEG. For PDFs it echoes the file back (mock).
  - `POST /api/watermark/remove` — accepts `file` and returns the same file as `removed-<name>` (mock).

Quick start (python 3.10+ recommended):

```bash
cd backend/fastapi
python -m venv .venv
source .venv/bin/activate    # on Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 4001
```

Frontend can point `VITE_API_BASE` to `http://localhost:4001` to use this FastAPI mock instead of the Node mock.
